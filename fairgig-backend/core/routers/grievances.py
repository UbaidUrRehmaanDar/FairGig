from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi import HTTPException
from pydantic import BaseModel, Field

from auth_middleware import get_current_user, require_role
from db import get_pool

try:
    import asyncpg  # type: ignore
    ForeignKeyViolationError = asyncpg.ForeignKeyViolationError
except ModuleNotFoundError:  # pragma: no cover
    asyncpg = None

    class ForeignKeyViolationError(Exception):
        pass

router = APIRouter()


class GrievanceIn(BaseModel):
    platform: str
    category: str
    title: str
    description: str
    tags: List[str] = Field(default_factory=list)


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


@router.post("/")
async def create_grievance(g: GrievanceIn, user=Depends(require_role("worker"))):
    try:
        pool = await get_pool()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable.") from exc

    try:
        row = await pool.fetchrow(
            """
            INSERT INTO grievances (
                worker_id,
                platform,
                category,
                title,
                description,
                tags
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING
                id,
                worker_id,
                platform,
                category,
                title,
                description,
                tags,
                status,
                upvotes,
                created_at,
                updated_at
            """,
            user["id"],
            g.platform,
            g.category,
            g.title,
            g.description,
            g.tags,
        )
    except ForeignKeyViolationError as exc:
        raise HTTPException(
            status_code=400,
            detail="Worker profile missing. Complete /auth/setup-profile first.",
        ) from exc

    return {
        "id": str(row["id"]),
        "worker_id": str(row["worker_id"]),
        "platform": row["platform"],
        "category": row["category"],
        "title": row["title"],
        "description": row["description"],
        "tags": row["tags"],
        "status": row["status"],
        "upvotes": row["upvotes"],
        "created_at": _to_json(row["created_at"]),
        "updated_at": _to_json(row["updated_at"]),
    }


@router.get("/")
async def list_grievances(
    platform: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
):
    try:
        pool = await get_pool()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable.") from exc

    clauses = ["1=1"]
    params: List[Any] = []

    if platform:
        params.append(platform)
        clauses.append(f"g.platform = ${len(params)}")
    if category:
        params.append(category)
        clauses.append(f"g.category = ${len(params)}")
    if status:
        params.append(status)
        clauses.append(f"g.status = ${len(params)}")

    where_sql = " AND ".join(clauses)

    rows = await pool.fetch(
        f"""
        SELECT
            g.id,
            g.worker_id,
            g.platform,
            g.category,
            g.title,
            g.description,
            g.tags,
            g.status,
            g.upvotes,
            g.created_at,
            g.updated_at,
            p.full_name,
            p.city_zone
        FROM grievances g
        LEFT JOIN profiles p ON p.id = g.worker_id
        WHERE {where_sql}
        ORDER BY g.created_at DESC
        LIMIT 200
        """,
        *params,
    )

    items = [_serialize_row(row) for row in rows]

    return {
        "items": items,
        "count": len(items),
        "filters": {
            "platform": platform,
            "category": category,
            "status": status,
        },
    }


@router.patch("/{grievance_id}/escalate")
async def escalate(grievance_id: str, user=Depends(require_role("advocate"))):
    try:
        grievance_uuid = UUID(grievance_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid grievance_id format") from exc

    try:
        pool = await get_pool()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable.") from exc
    row = await pool.fetchrow(
        """
        UPDATE grievances
        SET status = 'escalated', updated_at = NOW()
        WHERE id = $1
        RETURNING id, status, updated_at
        """,
        grievance_uuid,
    )

    if row is None:
        raise HTTPException(status_code=404, detail="Grievance not found")

    return {
        "status": row["status"],
        "grievance_id": str(row["id"]),
        "escalated_by": user["id"],
        "updated_at": _to_json(row["updated_at"]),
    }


@router.post("/{grievance_id}/upvote")
async def upvote(grievance_id: str, user=Depends(get_current_user)):
    try:
        grievance_uuid = UUID(grievance_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid grievance_id format") from exc

    try:
        pool = await get_pool()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable.") from exc
    row = await pool.fetchrow(
        """
        UPDATE grievances
        SET upvotes = upvotes + 1, updated_at = NOW()
        WHERE id = $1
        RETURNING id, upvotes, updated_at
        """,
        grievance_uuid,
    )

    if row is None:
        raise HTTPException(status_code=404, detail="Grievance not found")

    return {
        "ok": True,
        "grievance_id": str(row["id"]),
        "upvotes": row["upvotes"],
        "user_id": user["id"],
        "updated_at": _to_json(row["updated_at"]),
    }
