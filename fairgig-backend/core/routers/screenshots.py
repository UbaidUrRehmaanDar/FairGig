import os
from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

try:
    from supabase import Client, create_client
except Exception:
    # Keep core API bootable even if optional storage dependency is missing.
    Client = Any
    create_client = None

from auth_middleware import get_current_user, require_role
from db import get_pool

router = APIRouter()

ALLOWED_REVIEW_STATUS = {"verified", "flagged", "unverifiable"}
SHIFT_STATUS_BY_SCREENSHOT_STATUS = {
    "verified": "verified",
    "flagged": "disputed",
    "unverifiable": "unverified",
}

_supabase_client: Optional[Client] = None


class ScreenshotReviewIn(BaseModel):
    status: Literal["verified", "flagged", "unverifiable"]
    note: str = ""


def get_supabase_client() -> Client:
    global _supabase_client
    if create_client is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Screenshot storage dependency missing. "
                "Install backend package 'supabase' to enable screenshot upload/view."
            ),
        )

    if _supabase_client is None:
        supabase_url = (os.getenv("SUPABASE_URL") or "").strip()
        service_key = (os.getenv("SUPABASE_SERVICE_KEY") or "").strip()
        if not supabase_url or not service_key:
            raise HTTPException(
                status_code=500,
                detail="Supabase storage is not configured",
            )
        _supabase_client = create_client(supabase_url, service_key)
    return _supabase_client


def _get_bucket_name() -> str:
    return (os.getenv("SUPABASE_SCREENSHOT_BUCKET") or "earnings").strip() or "earnings"


def _extract_signed_url(value: Any) -> Optional[str]:
    if isinstance(value, dict):
        return value.get("signedURL") or value.get("signedUrl")

    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return data.get("signedURL") or data.get("signedUrl")

    return None


def _to_absolute_signed_url(signed_url: str) -> str:
    if signed_url.startswith("http://") or signed_url.startswith("https://"):
        return signed_url

    supabase_url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    if signed_url.startswith("/") and supabase_url:
        return f"{supabase_url}/storage/v1{signed_url}"

    return signed_url


@router.post("/upload/{shift_id}")
async def upload_screenshot(
    shift_id: str,
    file: UploadFile = File(...),
    user=Depends(require_role("worker")),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required")

    pool = await get_pool()
    shift = await pool.fetchrow(
        "SELECT id FROM shifts WHERE id = $1 AND worker_id = $2",
        shift_id,
        user["id"],
    )
    if shift is None:
        raise HTTPException(
            status_code=404,
            detail="Shift not found for this worker",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
    storage_path = f"screenshots/{user['id']}/{shift_id}/{uuid4()}.{extension}"

    storage = get_supabase_client().storage.from_(_get_bucket_name())
    try:
        storage.upload(
            storage_path,
            content,
            {"content-type": file.content_type or "application/octet-stream"},
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Failed to upload to storage") from exc

    screenshot = await pool.fetchrow(
        """
        INSERT INTO earnings_screenshots (shift_id, worker_id, storage_path, status)
        VALUES ($1, $2, $3, 'pending')
        RETURNING id, status, created_at
        """,
        shift_id,
        user["id"],
        storage_path,
    )

    await pool.execute(
        "UPDATE shifts SET verification_status = 'pending' WHERE id = $1",
        shift_id,
    )

    return {
        "status": "uploaded",
        "screenshot_id": str(screenshot["id"]),
        "shift_id": shift_id,
        "storage_path": storage_path,
        "review_status": screenshot["status"],
        "created_at": screenshot["created_at"],
        "filename": file.filename,
        "worker_id": user["id"],
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
            s.net_received,
            p.full_name,
            p.city_zone
        FROM earnings_screenshots es
        JOIN shifts s ON s.id = es.shift_id
        LEFT JOIN profiles p ON p.id = es.worker_id
        WHERE es.status = 'pending'
        ORDER BY es.created_at ASC
        LIMIT 100
        """
    )

    return [dict(row) for row in rows]


@router.patch("/{screenshot_id}/review")
async def review_screenshot(
    screenshot_id: str,
    review: ScreenshotReviewIn,
    user=Depends(require_role("verifier", "advocate")),
):
    if review.status not in ALLOWED_REVIEW_STATUS:
        raise HTTPException(status_code=400, detail="Invalid status")

    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT id, shift_id FROM earnings_screenshots WHERE id = $1",
        screenshot_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Screenshot not found")

    reviewed_at = datetime.utcnow()
    await pool.execute(
        """
        UPDATE earnings_screenshots
        SET
            status = $1,
            verifier_note = $2,
            verifier_id = $3,
            reviewed_at = $4
        WHERE id = $5
        """,
        review.status,
        review.note,
        user["id"],
        reviewed_at,
        screenshot_id,
    )

    await pool.execute(
        "UPDATE shifts SET verification_status = $1 WHERE id = $2",
        SHIFT_STATUS_BY_SCREENSHOT_STATUS[review.status],
        row["shift_id"],
    )

    return {
        "status": "updated",
        "screenshot_id": screenshot_id,
        "shift_id": str(row["shift_id"]),
        "review_status": review.status,
        "note": review.note,
        "reviewed_by": user["id"],
        "reviewed_at": reviewed_at,
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

    bucket = _get_bucket_name()
    storage = get_supabase_client().storage.from_(bucket)
    expires_in = 60

    try:
        signed_result = storage.create_signed_url(
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
