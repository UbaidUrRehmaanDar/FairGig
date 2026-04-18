import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from supabase import create_client

from auth_middleware import get_current_user, require_role
from db import get_pool

router = APIRouter()

_supabase_client = None


class ScreenshotReviewIn(BaseModel):
    status: Literal["verified", "flagged", "unverifiable"]
    note: str = ""


def _to_json(value: Any):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _serialize_row(row):
    return {key: _to_json(row[key]) for key in row.keys()}


def _get_bucket_name() -> str:
    return (os.getenv("SUPABASE_SCREENSHOT_BUCKET") or "earnings").strip() or "earnings"


def _get_storage_client():
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    supabase_url = (os.getenv("SUPABASE_URL") or "").strip()
    service_key = (os.getenv("SUPABASE_SERVICE_KEY") or "").strip()

    if not supabase_url or not service_key:
        raise HTTPException(status_code=500, detail="Supabase storage is not configured")

    _supabase_client = create_client(supabase_url, service_key)
    return _supabase_client


def _extract_signed_url(value: Any) -> str | None:
    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        return value.get("signedURL") or value.get("signedUrl")

    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return data.get("signedURL") or data.get("signedUrl")

    return None


def _to_absolute_signed_url(url: str) -> str:
    if url.startswith("http://") or url.startswith("https://"):
        return url

    supabase_url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    if url.startswith("/") and supabase_url:
        return f"{supabase_url}/storage/v1{url}"

    return url


async def _ensure_profile_exists(conn, user_id: str, role: str):
    await conn.execute(
        """
        INSERT INTO profiles (id, role)
        VALUES ($1, $2)
        ON CONFLICT (id) DO NOTHING
        """,
        user_id,
        role,
    )


@router.post("/upload/{shift_id}")
async def upload_screenshot(
    shift_id: str,
    file: UploadFile = File(...),
    user=Depends(require_role("worker")),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required")

    try:
        shift_uuid = UUID(shift_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid shift_id format") from exc

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    pool = await get_pool()

    async with pool.acquire() as conn:
        shift = await conn.fetchrow(
            """
            SELECT id, worker_id
            FROM shifts
            WHERE id = $1
            """,
            shift_uuid,
        )

        if shift is None:
            raise HTTPException(status_code=404, detail="Shift not found")

        if str(shift["worker_id"]) != user["id"]:
            raise HTTPException(status_code=403, detail="Cannot upload screenshot for another worker")

    suffix = Path(file.filename).suffix
    object_path = f"{user['id']}/{shift_uuid}/{uuid4().hex}{suffix}"
    bucket = _get_bucket_name()

    storage = _get_storage_client()
    try:
        storage.storage.from_(bucket).upload(
            object_path,
            file_bytes,
            {
                "content-type": file.content_type or "application/octet-stream",
                "upsert": "false",
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Storage upload failed: {exc}") from exc

    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                INSERT INTO earnings_screenshots (
                    shift_id,
                    worker_id,
                    storage_path,
                    status
                )
                VALUES ($1, $2, $3, 'pending')
                RETURNING id, shift_id, worker_id, storage_path, status, created_at
                """,
                shift_uuid,
                user["id"],
                object_path,
            )

            await conn.execute(
                """
                UPDATE shifts
                SET verification_status = 'pending'
                WHERE id = $1
                """,
                shift_uuid,
            )

    return {
        "status": "uploaded",
        "screenshot_id": str(row["id"]),
        "shift_id": str(row["shift_id"]),
        "storage_path": row["storage_path"],
        "worker_id": str(row["worker_id"]),
        "review_status": row["status"],
        "created_at": _to_json(row["created_at"]),
        "bucket": bucket,
    }


@router.get("/pending")
async def pending_screenshots(user=Depends(require_role("verifier", "advocate"))):
    pool = await get_pool()

    rows = await pool.fetch(
        """
        SELECT
            es.id,
            es.shift_id,
            es.worker_id,
            es.storage_path,
            es.status,
            es.created_at,
            s.platform,
            s.shift_date,
            s.gross_earned,
            s.platform_deductions,
            s.net_received,
            s.verification_status,
            p.full_name,
            p.city_zone
        FROM earnings_screenshots es
        JOIN shifts s ON s.id = es.shift_id
        LEFT JOIN profiles p ON p.id = es.worker_id
        WHERE es.status = 'pending'
        ORDER BY es.created_at ASC
        """
    )

    items = [_serialize_row(row) for row in rows]
    return {"items": items, "count": len(items)}


@router.patch("/{screenshot_id}/review")
async def review_screenshot(
    screenshot_id: str,
    payload: ScreenshotReviewIn,
    user=Depends(require_role("verifier", "advocate")),
):
    try:
        screenshot_uuid = UUID(screenshot_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid screenshot_id format") from exc

    pool = await get_pool()

    shift_status = "verified" if payload.status == "verified" else "disputed"

    async with pool.acquire() as conn:
        async with conn.transaction():
            await _ensure_profile_exists(conn, user["id"], user["role"])

            screenshot = await conn.fetchrow(
                """
                SELECT id, shift_id
                FROM earnings_screenshots
                WHERE id = $1
                """,
                screenshot_uuid,
            )

            if screenshot is None:
                raise HTTPException(status_code=404, detail="Screenshot not found")

            updated = await conn.fetchrow(
                """
                UPDATE earnings_screenshots
                SET
                    status = $2,
                    verifier_id = $3,
                    verifier_note = $4,
                    reviewed_at = NOW()
                WHERE id = $1
                RETURNING
                    id,
                    shift_id,
                    worker_id,
                    status,
                    verifier_id,
                    verifier_note,
                    reviewed_at
                """,
                screenshot_uuid,
                payload.status,
                user["id"],
                payload.note,
            )

            await conn.execute(
                """
                UPDATE shifts
                SET verification_status = $2
                WHERE id = $1
                """,
                screenshot["shift_id"],
                shift_status,
            )

    return {
        "status": "updated",
        "screenshot": _serialize_row(updated),
        "shift_verification_status": shift_status,
        "reviewed_by": user["id"],
    }


@router.get("/view/{screenshot_id}")
async def view_screenshot(
    screenshot_id: str,
    redirect: bool = True,
    user=Depends(get_current_user),
):
    try:
        screenshot_uuid = UUID(screenshot_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid screenshot_id format") from exc

    pool = await get_pool()

    async with pool.acquire() as conn:
        screenshot = await conn.fetchrow(
            """
            SELECT id, worker_id, storage_path, status
            FROM earnings_screenshots
            WHERE id = $1
            """,
            screenshot_uuid,
        )

    if screenshot is None:
        raise HTTPException(status_code=404, detail="Screenshot not found")

    is_privileged = user["role"] in {"verifier", "advocate"}
    is_owner = str(screenshot["worker_id"]) == user["id"]
    if not is_privileged and not is_owner:
        raise HTTPException(status_code=403, detail="Cannot view screenshot for another worker")

    storage = _get_storage_client()
    bucket = _get_bucket_name()
    expires_in = 60

    try:
        signed_result = storage.storage.from_(bucket).create_signed_url(
            screenshot["storage_path"],
            expires_in,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not generate access link: {exc}") from exc

    signed_url = _extract_signed_url(signed_result)
    if not signed_url:
        raise HTTPException(status_code=502, detail="Could not generate access link")

    signed_url = _to_absolute_signed_url(signed_url)

    if redirect:
        return RedirectResponse(url=signed_url, status_code=307)

    return {
        "screenshot_id": str(screenshot["id"]),
        "worker_id": str(screenshot["worker_id"]),
        "bucket": bucket,
        "storage_path": screenshot["storage_path"],
        "signed_url": signed_url,
        "expires_in": expires_in,
    }
