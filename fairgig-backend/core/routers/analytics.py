from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends

from auth_middleware import require_role
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


@router.get("/kpis")
async def kpis(user=Depends(require_role("advocate"))):
    try:
        pool = await get_pool()
    except Exception:
        return {
            "commission_trends": [],
            "income_by_zone": [],
            "vulnerability_flags": [],
            "top_complaints": [],
        }

    commission_trends_rows = await pool.fetch(
        """
        SELECT
            shift_date,
            COALESCE(
                AVG((platform_deductions / NULLIF(gross_earned, 0)) * 100),
                0
            ) AS avg_commission_pct,
            COUNT(*)::int AS sample_size
        FROM shifts
        GROUP BY shift_date
        ORDER BY shift_date DESC
        LIMIT 30
        """
    )

    income_by_zone_rows = await pool.fetch(
        """
        SELECT
            COALESCE(p.city_zone, 'Unknown') AS city_zone,
            COALESCE(SUM(s.net_received), 0) AS total_net_received,
            COALESCE(AVG(s.net_received), 0) AS avg_net_received,
            COUNT(*)::int AS sample_size,
            COUNT(DISTINCT s.worker_id)::int AS worker_count
        FROM shifts s
        JOIN profiles p ON p.id = s.worker_id
        GROUP BY COALESCE(p.city_zone, 'Unknown')
        ORDER BY total_net_received DESC
        LIMIT 20
        """
    )

    vulnerability_rows = await pool.fetch(
        """
        WITH ordered AS (
            SELECT
                s.worker_id,
                s.platform,
                s.shift_date,
                s.net_received,
                LAG(s.net_received) OVER (
                    PARTITION BY s.worker_id
                    ORDER BY s.shift_date, s.created_at
                ) AS prev_net_received
            FROM shifts s
        )
        SELECT
            o.worker_id,
            p.full_name,
            p.city_zone,
            o.platform,
            o.shift_date,
            o.prev_net_received,
            o.net_received,
            ((o.prev_net_received - o.net_received) / NULLIF(o.prev_net_received, 0)) * 100
                AS income_drop_pct
        FROM ordered o
        LEFT JOIN profiles p ON p.id = o.worker_id
        WHERE o.prev_net_received IS NOT NULL
          AND o.prev_net_received > 0
          AND ((o.prev_net_received - o.net_received) / o.prev_net_received) > 0.20
        ORDER BY income_drop_pct DESC, o.shift_date DESC
        LIMIT 50
        """
    )

    top_complaints_rows = await pool.fetch(
        """
        SELECT
            category,
            COUNT(*)::int AS total_count,
            COALESCE(SUM(upvotes), 0)::int AS total_upvotes
        FROM grievances
        GROUP BY category
        ORDER BY total_count DESC, total_upvotes DESC, category ASC
        LIMIT 10
        """
    )

    return {
        "commission_trends": [_serialize_row(row) for row in commission_trends_rows],
        "income_by_zone": [_serialize_row(row) for row in income_by_zone_rows],
        "vulnerability_flags": [_serialize_row(row) for row in vulnerability_rows],
        "top_complaints": [_serialize_row(row) for row in top_complaints_rows],
    }
