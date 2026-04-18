from datetime import date
from decimal import Decimal
from typing import Any, Dict

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from auth_middleware import require_role
from db import get_pool

router = APIRouter()


@router.get("/data")
async def certificate_data(
    start_date: date,
    end_date: date,
    user=Depends(require_role("worker")),
):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date cannot be after end_date")

    pool = await get_pool()

    profile = await pool.fetchrow(
        """
        SELECT
            id,
            full_name,
            city_zone,
            platform_category,
            role
        FROM profiles
        WHERE id = $1
        """,
        user["id"],
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Worker profile not found. Complete /auth/setup-profile first.",
        )

    rows = await pool.fetch(
        """
        SELECT
            id,
            shift_date,
            platform,
            hours_worked,
            gross_earned,
            platform_deductions,
            net_received,
            verification_status,
            notes,
            created_at
        FROM shifts
        WHERE worker_id = $1
          AND verification_status = 'verified'
          AND shift_date >= $2
          AND shift_date <= $3
        ORDER BY shift_date ASC, created_at ASC
        """,
        user["id"],
        start_date,
        end_date,
    )

    summary_row = await pool.fetchrow(
        """
        SELECT
            COALESCE(SUM(gross_earned), 0) AS total_gross,
            COALESCE(SUM(net_received), 0) AS total_net,
            COUNT(*)::int AS total_shifts,
            COALESCE(SUM(hours_worked), 0) AS total_hours,
            COALESCE(
                AVG(platform_deductions / NULLIF(gross_earned, 0)) * 100,
                0
            ) AS avg_commission_pct
        FROM shifts
        WHERE worker_id = $1
          AND verification_status = 'verified'
          AND shift_date >= $2
          AND shift_date <= $3
        """,
        user["id"],
        start_date,
        end_date,
    )

    shifts = [_serialize_row(row) for row in rows]
    summary = _serialize_row(summary_row) if summary_row else {}

    return {
        "worker": {
            "id": str(profile["id"]),
            "full_name": profile["full_name"],
            "city_zone": profile["city_zone"],
            "platform_category": profile["platform_category"],
            "role": profile["role"],
        },
        "period": {"start": str(start_date), "end": str(end_date)},
        "shifts": shifts,
        "summary": {
            "total_gross": float(summary.get("total_gross") or 0),
            "total_net": float(summary.get("total_net") or 0),
            "total_shifts": int(summary.get("total_shifts") or 0),
            "total_hours": float(summary.get("total_hours") or 0),
            "avg_commission_pct": float(summary.get("avg_commission_pct") or 0),
        },
    }


def _to_json(value: Any):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date):
        return value.isoformat()
    return value


def _serialize_row(row: asyncpg.Record) -> Dict[str, Any]:
    return {key: _to_json(row[key]) for key in row.keys()}
