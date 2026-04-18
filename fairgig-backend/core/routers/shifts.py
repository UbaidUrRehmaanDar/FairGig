from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from auth_middleware import require_role
from db import get_pool

try:
    import asyncpg  # type: ignore
    ForeignKeyViolationError = asyncpg.ForeignKeyViolationError
except ModuleNotFoundError:  # pragma: no cover
    asyncpg = None

    class ForeignKeyViolationError(Exception):
        pass

router = APIRouter()

ANOMALY_TIMEOUT_SECONDS = 8.0
ANOMALY_DEFAULT_LIMIT = 120
ANOMALY_MAX_LIMIT = 240


def _to_json(value: Any):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date,)):
        return value.isoformat()
    return value


def _serialize_row(row: Any) -> dict:
    return {key: _to_json(row[key]) for key in row.keys()}


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def _normalize_severity(value: Any) -> str:
    normalized = str(value or 'medium').strip().lower()
    if normalized in {'critical', 'high', 'medium', 'low'}:
        return normalized
    return 'medium'


def _normalize_anomaly_entry(raw: Any) -> dict:
    entry = raw if isinstance(raw, dict) else {}
    value = entry.get('value')

    if isinstance(value, Decimal):
        normalized_value: Any = float(value)
    elif value is None:
        normalized_value = None
    else:
        normalized_value = value

    return {
        'date': str(entry.get('date') or ''),
        'platform': str(entry.get('platform') or 'Unknown platform'),
        'type': str(entry.get('type') or 'anomaly'),
        'severity': _normalize_severity(entry.get('severity')),
        'value': normalized_value,
        'explanation': str(entry.get('explanation') or 'No explanation provided.'),
    }


def _to_earnings_payload_row(row: dict) -> dict:
    return {
        'date': str(row.get('shift_date') or ''),
        'platform': str(row.get('platform') or 'Unknown platform'),
        'gross_earned': _to_float(row.get('gross_earned')),
        'platform_deductions': _to_float(row.get('platform_deductions')),
        'net_received': _to_float(row.get('net_received')),
        'hours_worked': None if row.get('hours_worked') is None else _to_float(row.get('hours_worked')),
    }


def _avg_commission_pct(rows: list[dict]) -> float:
    ratios = []
    for row in rows:
        gross = _to_float(row.get('gross_earned'))
        if gross <= 0:
            continue
        ratios.append((_to_float(row.get('platform_deductions')) / gross) * 100)

    if not ratios:
        return 0.0
    return float(sum(ratios) / len(ratios))


async def _call_anomaly_service(worker_id: str, earnings_payload: list[dict]):
    anomaly_service_url = (os.getenv('ANOMALY_SERVICE_URL') or '').strip()
    if not anomaly_service_url:
        environment = (os.getenv('ENVIRONMENT') or 'development').strip().lower()
        if environment == 'development':
            anomaly_service_url = 'http://127.0.0.1:8001'
        else:
            return [], 'unavailable', 'Anomaly service is not configured.'

    endpoints = [
        f"{anomaly_service_url.rstrip('/')}/anomaly/detect",
        f"{anomaly_service_url.rstrip('/')}/detect",
    ]

    payload = None
    last_status = 'unknown'

    try:
        async with httpx.AsyncClient(timeout=ANOMALY_TIMEOUT_SECONDS) as client:
            for endpoint in endpoints:
                try:
                    response = await client.post(
                        endpoint,
                        json={'worker_id': worker_id, 'earnings': earnings_payload},
                    )
                    response.raise_for_status()
                    payload = response.json() if response.content else {}
                    break
                except httpx.HTTPStatusError as exc:
                    last_status = str(exc.response.status_code) if exc.response is not None else 'unknown'
                    if exc.response is None or exc.response.status_code != 404:
                        raise
                except httpx.TimeoutException:
                    raise
    except httpx.TimeoutException:
        return [], 'timeout', 'Anomaly service timed out.'
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else last_status
        return [], 'error', f'Anomaly service failed ({status}).'
    except Exception:
        return [], 'error', 'Anomaly service is currently unavailable.'

    if payload is None:
        return [], 'error', f'Anomaly service failed ({last_status}).'

    findings_raw = payload.get('anomalies') if isinstance(payload, dict) else []
    findings = [
        _normalize_anomaly_entry(item)
        for item in findings_raw
        if isinstance(item, dict)
    ]
    return findings, 'ok', None


async def _build_worker_anomaly_check(pool: Any, worker_id: str, limit: int) -> dict:
    rows = await pool.fetch(
        """
        SELECT
            shift_date,
            platform,
            gross_earned,
            platform_deductions,
            net_received,
            hours_worked,
            created_at
        FROM shifts
        WHERE worker_id = $1
        ORDER BY shift_date DESC, created_at DESC
        LIMIT $2
        """,
        worker_id,
        limit,
    )

    serialized_rows = [_serialize_row(row) for row in rows]
    earnings_payload = [_to_earnings_payload_row(row) for row in reversed(serialized_rows)]

    findings: list[dict] = []
    service_status = 'ok'
    service_message = None

    if len(earnings_payload) >= 2:
        findings, service_status, service_message = await _call_anomaly_service(
            worker_id,
            earnings_payload,
        )
    else:
        service_status = 'insufficient_data'
        service_message = 'At least two shifts are required for anomaly analysis.'

    high_priority_flags = sum(
        1
        for item in findings
        if str(item.get('severity') or '').lower() in {'high', 'critical'}
    )
    total_net = sum(_to_float(row.get('net_received')) for row in serialized_rows)

    return {
        'worker_id': worker_id,
        'scanned_at': _utc_now_iso(),
        'window_limit': limit,
        'service_status': service_status,
        'service_message': service_message,
        'summary': {
            'shifts_analyzed': len(serialized_rows),
            'high_priority_flags': high_priority_flags,
            'avg_commission_pct': round(_avg_commission_pct(serialized_rows), 1),
            'total_net': round(total_net, 2),
        },
        'findings_count': len(findings),
        'findings': findings,
        'public_api': {
            'endpoint': '/anomaly/detect',
            'description': 'The detection logic runs at /anomaly/detect, with /detect as a fallback for older sidecars.',
        },
    }


class ShiftIn(BaseModel):
    platform: str
    shift_date: date
    hours_worked: Optional[float] = None
    gross_earned: float
    platform_deductions: float = 0
    net_received: float
    notes: Optional[str] = None


@router.post("/")
async def log_shift(shift: ShiftIn, user=Depends(require_role("worker"))):
    try:
        pool = await get_pool()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable.") from exc

    try:
        row = await pool.fetchrow(
            """
            INSERT INTO shifts (
                worker_id,
                platform,
                shift_date,
                hours_worked,
                gross_earned,
                platform_deductions,
                net_received,
                notes
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            user["id"],
            shift.platform,
            shift.shift_date,
            shift.hours_worked,
            shift.gross_earned,
            shift.platform_deductions,
            shift.net_received,
            shift.notes,
        )
    except ForeignKeyViolationError as exc:
        raise HTTPException(
            status_code=400,
            detail="Worker profile missing. Complete /auth/setup-profile first.",
        ) from exc

    anomaly_service_url = (os.getenv("ANOMALY_SERVICE_URL") or "").strip()
    if anomaly_service_url:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                await client.post(
                    f"{anomaly_service_url.rstrip('/')}/detect/single",
                    json={"shift_id": str(row["id"]), **shift.model_dump()},
                )
        except Exception:
            # Do not block shift creation on anomaly sidecar availability.
            pass

    return {
        "shift_id": str(row["id"]),
        "status": "logged",
        "worker_id": user["id"],
        "payload": shift.model_dump(),
    }


@router.get("/")
async def list_shifts(user=Depends(require_role("worker"))):
    try:
        pool = await get_pool()
    except Exception:
        return []

    rows = await pool.fetch(
        """
        SELECT
            id,
            worker_id,
            platform,
            shift_date,
            hours_worked,
            gross_earned,
            platform_deductions,
            net_received,
            notes,
            verification_status,
            created_at
        FROM shifts
        WHERE worker_id = $1
        ORDER BY shift_date DESC, created_at DESC
        LIMIT 200
        """,
        user["id"],
    )

    return [dict(row) for row in rows]


@router.get("/summary")
async def shift_summary(user=Depends(require_role("worker"))):
    try:
        pool = await get_pool()
    except Exception:
        return {
            "this_month": 0,
            "this_week": 0,
            "avg_hourly": 0,
            "avg_commission_pct": 0,
            "total_shifts": 0,
        }
    row = await pool.fetchrow(
        """
        SELECT
            COALESCE(
                SUM(net_received) FILTER (
                    WHERE shift_date >= date_trunc('month', CURRENT_DATE)::date
                ),
                0
            ) AS this_month,
            COALESCE(
                SUM(net_received) FILTER (
                    WHERE shift_date >= date_trunc('week', CURRENT_DATE)::date
                ),
                0
            ) AS this_week,
            COALESCE(AVG(net_received / NULLIF(hours_worked, 0)), 0) AS avg_hourly,
            COALESCE(
                AVG(platform_deductions / NULLIF(gross_earned, 0)) * 100,
                0
            ) AS avg_commission_pct,
            COUNT(*)::int AS total_shifts
        FROM shifts
        WHERE worker_id = $1
        """,
        user["id"],
    )

    if row is None:
        return {
            "this_month": 0,
            "this_week": 0,
            "avg_hourly": 0,
            "avg_commission_pct": 0,
            "total_shifts": 0,
        }

    result = dict(row)
    return {
        "this_month": float(result.get("this_month") or 0),
        "this_week": float(result.get("this_week") or 0),
        "avg_hourly": float(result.get("avg_hourly") or 0),
        "avg_commission_pct": float(result.get("avg_commission_pct") or 0),
        "total_shifts": int(result.get("total_shifts") or 0),
    }


@router.get("/city-median")
async def city_median(platform: str, user=Depends(require_role("worker"))):
    try:
        pool = await get_pool()
    except Exception:
        return {
            "platform": platform,
            "city_zone": None,
            "platform_category": None,
            "median_hourly": None,
            "median_daily": None,
            "avg_commission_pct": None,
            "sample_size": 0,
            "note": "Database is unavailable.",
        }

    profile = await pool.fetchrow(
        "SELECT city_zone, platform_category FROM profiles WHERE id = $1",
        user["id"],
    )
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Worker profile not found. Complete /auth/setup-profile first.",
        )

    row = await pool.fetchrow(
        """
        SELECT
            median_hourly,
            median_daily,
            avg_commission_pct,
            sample_size
        FROM city_medians
        WHERE platform = $1
          AND city_zone = $2
          AND platform_category = $3
          AND month = date_trunc('month', CURRENT_DATE)
        LIMIT 1
        """,
        platform,
        profile["city_zone"],
        profile["platform_category"],
    )

    if row is None:
        return {
            "platform": platform,
            "city_zone": profile["city_zone"],
            "platform_category": profile["platform_category"],
            "median_hourly": None,
            "median_daily": None,
            "avg_commission_pct": None,
            "sample_size": 0,
            "note": "No current-month city median found for this platform and zone.",
        }

    result = dict(row)
    return {
        "platform": platform,
        "city_zone": profile["city_zone"],
        "platform_category": profile["platform_category"],
        "median_hourly": float(result.get("median_hourly") or 0),
        "median_daily": float(result.get("median_daily") or 0),
        "avg_commission_pct": float(result.get("avg_commission_pct") or 0),
        "sample_size": int(result.get("sample_size") or 0),
    }


@router.get("/anomaly-check")
async def anomaly_check(
    limit: int = Query(ANOMALY_DEFAULT_LIMIT, ge=1, le=ANOMALY_MAX_LIMIT),
    user=Depends(require_role("worker")),
):
    try:
        pool = await get_pool()
    except Exception:
        return {
            "worker_id": user["id"],
            "scanned_at": _utc_now_iso(),
            "window_limit": limit,
            "service_status": "unavailable",
            "service_message": "Database is unavailable.",
            "summary": {
                "shifts_analyzed": 0,
                "high_priority_flags": 0,
                "avg_commission_pct": 0.0,
                "total_net": 0.0,
            },
            "findings_count": 0,
            "findings": [],
            "public_api": {
                "endpoint": "/anomaly/detect",
                "description": "Anomaly detection runs on the sidecar when shift history is available.",
            },
        }

    return await _build_worker_anomaly_check(pool, user["id"], limit)
