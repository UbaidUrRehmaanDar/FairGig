from datetime import date
from decimal import Decimal
from typing import Any, Optional

import os

import asyncpg
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth_middleware import require_role
from db import get_pool

router = APIRouter()


def _to_json(value: Any):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date,)):
        return value.isoformat()
    return value


def _serialize_row(row: asyncpg.Record) -> dict:
    return {key: _to_json(row[key]) for key in row.keys()}


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
    pool = await get_pool()

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
    except asyncpg.ForeignKeyViolationError as exc:
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
    pool = await get_pool()

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
    pool = await get_pool()
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
    pool = await get_pool()

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
