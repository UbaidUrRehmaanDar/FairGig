from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from auth_middleware import get_current_user
from db import get_pool

try:
    import asyncpg  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    asyncpg = None

router = APIRouter()


def _to_json(value: Any):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def _serialize_row(row: Any) -> dict:
    return {key: _to_json(row[key]) for key in row.keys()}


@router.get("/data")
async def certificate_data(
    start_date: date,
    end_date: date,
    user=Depends(get_current_user),
):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be on or before end_date")

    try:
        pool = await get_pool()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable.") from exc

    profile = await pool.fetchrow(
        """
        SELECT
            id,
            full_name,
            city_zone,
            platform_category,
            role,
            created_at
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

    shifts = await pool.fetch(
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
          AND shift_date BETWEEN $2 AND $3
          AND verification_status = 'verified'
        ORDER BY shift_date ASC, created_at ASC
        """,
        user["id"],
        start_date,
        end_date,
    )

    totals = await pool.fetchrow(
        """
        SELECT
            COALESCE(SUM(gross_earned), 0) AS total_gross,
            COALESCE(SUM(net_received), 0) AS total_net,
            COUNT(*)::int AS total_shifts,
            COALESCE(SUM(hours_worked), 0) AS total_hours
        FROM shifts
        WHERE worker_id = $1
          AND shift_date BETWEEN $2 AND $3
          AND verification_status = 'verified'
        """,
        user["id"],
        start_date,
        end_date,
    )

    summary = _serialize_row(totals) if totals else {
        "total_gross": 0,
        "total_net": 0,
        "total_shifts": 0,
        "total_hours": 0,
    }

    return {
        "worker": _serialize_row(profile),
        "period": {"start": str(start_date), "end": str(end_date)},
        "shifts": [_serialize_row(row) for row in shifts],
        "summary": summary,
    }
