from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
import math
from typing import Any, Optional

import os

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator, model_validator

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


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _stddev(values: list[float], mean_value: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((value - mean_value) ** 2 for value in values) / len(values)
    return float(math.sqrt(variance))


def _deduction_pct(record: dict) -> float:
    gross = _to_float(record.get('gross_earned'))
    deductions = _to_float(record.get('platform_deductions'))
    if gross <= 0:
        return 0.0
    return (deductions / gross) * 100.0


def _detect_anomalies_locally(earnings_payload: list[dict]) -> list[dict]:
    findings: list[dict] = []
    if not earnings_payload:
        return findings

    ordered = sorted(earnings_payload, key=lambda x: str(x.get('date') or ''))
    deduction_pcts = [_deduction_pct(item) for item in ordered]

    for index in range(1, len(ordered)):
        baseline = deduction_pcts[:index]
        baseline_mean = _mean(baseline)
        baseline_std = _stddev(baseline, baseline_mean)
        if baseline_std < 1.0:
            baseline_std = 1.0

        current_pct = deduction_pcts[index]
        z_score = (current_pct - baseline_mean) / baseline_std
        if z_score > 2.0:
            severity = 'critical' if z_score >= 4.0 else 'high'
            findings.append(
                {
                    'date': ordered[index].get('date'),
                    'platform': ordered[index].get('platform'),
                    'type': 'unusual_deduction',
                    'severity': severity,
                    'value': round(z_score, 2),
                    'explanation': (
                        f"Deductions reached {current_pct:.1f}% of gross earnings, "
                        f"which is {z_score:.2f} standard deviations above prior shifts."
                    ),
                }
            )

    for index in range(1, len(ordered)):
        previous_net = _to_float(ordered[index - 1].get('net_received'))
        current_net = _to_float(ordered[index].get('net_received'))
        if previous_net <= 0:
            continue

        drop_pct = ((previous_net - current_net) / previous_net) * 100.0
        if drop_pct > 20.0:
            if drop_pct >= 50.0:
                severity = 'critical'
            elif drop_pct >= 35.0:
                severity = 'high'
            else:
                severity = 'medium'

            findings.append(
                {
                    'date': ordered[index].get('date'),
                    'platform': ordered[index].get('platform'),
                    'type': 'income_drop',
                    'severity': severity,
                    'value': round(drop_pct, 1),
                    'explanation': (
                        f"Net income dropped by {drop_pct:.1f}% compared to the previous "
                        f"shift ({previous_net:.2f} to {current_net:.2f})."
                    ),
                }
            )

    for record in ordered:
        gross = _to_float(record.get('gross_earned'))
        net = _to_float(record.get('net_received'))
        if gross > 0 and net <= 0:
            findings.append(
                {
                    'date': record.get('date'),
                    'platform': record.get('platform'),
                    'type': 'zero_net',
                    'severity': 'critical',
                    'value': round(net, 2),
                    'explanation': (
                        f"Gross earnings were {gross:.2f}, but net received was {net:.2f}. "
                        'This indicates full deduction or payout failure.'
                    ),
                }
            )

    return findings


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
        local_findings = _detect_anomalies_locally(earnings_payload)
        return local_findings, 'ok', None
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else last_status
        if status in {404, 500, 502, 503, 504}:
            local_findings = _detect_anomalies_locally(earnings_payload)
            return local_findings, 'ok', None
        return [], 'error', f'Anomaly service failed ({status}).'
    except Exception:
        local_findings = _detect_anomalies_locally(earnings_payload)
        return local_findings, 'ok', None

    if payload is None:
        local_findings = _detect_anomalies_locally(earnings_payload)
        return local_findings, 'ok', None

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
    net_received: Optional[float] = None
    notes: Optional[str] = None

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, value: str) -> str:
        allowed = {"careem", "indrive", "bykea", "foodpanda", "cheetay", "other"}
        cleaned = str(value or "").strip()
        if cleaned.lower() not in allowed:
            raise ValueError("platform is invalid")
        return cleaned

    @field_validator("hours_worked")
    @classmethod
    def validate_hours(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return value
        if value <= 0 or value > 24:
            raise ValueError("hours_worked must be > 0 and <= 24")
        return round(float(value), 2)

    @field_validator("gross_earned")
    @classmethod
    def validate_gross(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("gross_earned must be greater than 0")
        return round(float(value), 2)

    @field_validator("platform_deductions")
    @classmethod
    def validate_deductions(cls, value: float) -> float:
        if value < 0:
            raise ValueError("platform_deductions cannot be negative")
        return round(float(value), 2)

    @field_validator("net_received")
    @classmethod
    def validate_net(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return value
        if value < 0:
            raise ValueError("net_received cannot be negative")
        return round(float(value), 2)

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = " ".join(str(value).split()).strip()
        if len(cleaned) > 500:
            raise ValueError("notes must be 500 characters or fewer")
        return cleaned or None

    @model_validator(mode="after")
    def validate_consistency(self):
        if self.shift_date > date.today():
            raise ValueError("shift_date cannot be in the future")
        if self.platform_deductions > self.gross_earned:
            raise ValueError("platform_deductions cannot exceed gross_earned")
        computed_net = round(float(self.gross_earned) - float(self.platform_deductions), 2)
        if self.net_received is None:
            self.net_received = computed_net
        elif round(float(self.net_received), 2) != computed_net:
            raise ValueError("net_received must equal gross_earned minus platform_deductions")
        if self.net_received > self.gross_earned:
            raise ValueError("net_received cannot exceed gross_earned")
        return self


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
                notes,
                verification_status
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'verified')
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
