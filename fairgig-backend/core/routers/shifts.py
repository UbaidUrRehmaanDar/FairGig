from datetime import date
from decimal import Decimal
from typing import Any, Optional

import asyncpg
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
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'unverified')
        RETURNING
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

    return {
        "shift_id": str(row["id"]),
        "status": "logged",
        "shift": _serialize_row(row),
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
        """,
        user["id"],
    )

    items = [_serialize_row(row) for row in rows]
    return {"items": items, "count": len(items)}


@router.get("/summary")
async def shift_summary(user=Depends(require_role("worker"))):
    pool = await get_pool()

    row = await pool.fetchrow(
        """
        SELECT
            COALESCE(
                SUM(CASE
                    WHEN shift_date >= date_trunc('month', current_date)::date THEN net_received
                    ELSE 0
                END),
                0
            ) AS this_month,
            COALESCE(
                SUM(CASE
                    WHEN shift_date >= date_trunc('week', current_date)::date THEN net_received
                    ELSE 0
                END),
                0
            ) AS this_week,
            COALESCE(
                AVG(CASE
                    WHEN hours_worked > 0 THEN net_received / NULLIF(hours_worked, 0)
                    ELSE NULL
                END),
                0
            ) AS avg_hourly,
            COALESCE(
                AVG(CASE
                    WHEN gross_earned > 0 THEN (platform_deductions / NULLIF(gross_earned, 0)) * 100
                    ELSE NULL
                END),
                0
            ) AS avg_commission_pct,
            COUNT(*)::int AS total_shifts
        FROM shifts
        WHERE worker_id = $1
        """,
        user["id"],
    )

    return {
        "this_month": _to_json(row["this_month"]),
        "this_week": _to_json(row["this_week"]),
        "avg_hourly": _to_json(row["avg_hourly"]),
        "avg_commission_pct": _to_json(row["avg_commission_pct"]),
        "total_shifts": row["total_shifts"],
    }


@router.get("/city-median")
async def city_median(platform: str, user=Depends(require_role("worker"))):
    pool = await get_pool()

    profile = await pool.fetchrow(
        """
        SELECT city_zone, platform_category
        FROM profiles
        WHERE id = $1
        """,
        user["id"],
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Worker profile not found. Please complete setup-profile first.",
        )

    source = "city_medians"
    row = None

    try:
        row = await pool.fetchrow(
            """
            SELECT
              platform,
              platform_category,
              city_zone,
              month::date AS month,
              median_hourly,
              median_daily,
              avg_commission_pct,
              sample_size
            FROM city_medians
            WHERE platform = $1
              AND platform_category = $2
              AND city_zone = $3
            ORDER BY month DESC
            LIMIT 1
            """,
            platform,
            profile["platform_category"],
            profile["city_zone"],
        )
    except asyncpg.UndefinedTableError:
        source = "computed_fallback"

    if row is None:
        row = await pool.fetchrow(
            """
            WITH monthly AS (
              SELECT
                $1::text AS platform,
                p.platform_category,
                p.city_zone,
                date_trunc('month', s.shift_date)::date AS month,
                percentile_cont(0.5) WITHIN GROUP (
                  ORDER BY s.net_received / NULLIF(s.hours_worked, 0)
                ) AS median_hourly,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY s.net_received) AS median_daily,
                AVG(s.platform_deductions / NULLIF(s.gross_earned, 0)) * 100 AS avg_commission_pct,
                COUNT(*)::int AS sample_size
              FROM shifts s
              JOIN profiles p ON p.id = s.worker_id
              WHERE s.platform = $1
                AND p.platform_category = $2
                AND p.city_zone = $3
              GROUP BY date_trunc('month', s.shift_date)::date, p.platform_category, p.city_zone
            )
            SELECT *
            FROM monthly
            ORDER BY month DESC
            LIMIT 1
            """,
            platform,
            profile["platform_category"],
            profile["city_zone"],
        )

    if row is None:
        return {
            "platform": platform,
            "platform_category": profile["platform_category"],
            "city_zone": profile["city_zone"],
            "month": None,
            "median_hourly": None,
            "median_daily": None,
            "avg_commission_pct": None,
            "sample_size": 0,
            "source": source,
        }

    payload = _serialize_row(row)
    payload["source"] = source
    return payload
