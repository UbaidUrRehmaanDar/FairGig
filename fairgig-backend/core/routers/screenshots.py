import os
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, Optional
from urllib.parse import quote
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

try:
    from supabase import Client, create_client
except Exception:
    # Keep API bootable even when SDK import is unavailable.
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

_supabase_client: Optional[Any] = None
SUPABASE_SDK_KEY_PATTERN = re.compile(
    r"^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$"
)


class ScreenshotReviewIn(BaseModel):
    status: Literal["verified", "flagged", "unverifiable"]
    note: str = ""


def _get_storage_credentials() -> tuple[str, str]:
    supabase_url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    service_key = (
        os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or ""
    ).strip()

    if not supabase_url or not service_key:
        raise HTTPException(
            status_code=500,
            detail="Supabase storage is not configured",
        )

    return supabase_url, service_key


def _storage_headers(api_key: str, content_type: Optional[str] = None) -> dict[str, str]:
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def _response_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        text = (response.text or "").strip()
        return text or f"HTTP {response.status_code}"

    if isinstance(payload, dict):
        for key in ("detail", "message", "msg", "error"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return str(payload)


def _is_sdk_compatible_key(api_key: str) -> bool:
    return bool(SUPABASE_SDK_KEY_PATTERN.match(api_key))


def get_supabase_client() -> Any:
    global _supabase_client, create_client, Client
    if create_client is None:
        try:
            from supabase import Client as SupabaseClient, create_client as supabase_create_client

            Client = SupabaseClient
            create_client = supabase_create_client
        except Exception:
            try:
                from supabase.client import Client as SupabaseClient, create_client as supabase_create_client

                Client = SupabaseClient
                create_client = supabase_create_client
            except Exception:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Screenshot storage dependency missing. "
                        "Install backend package 'supabase' to enable screenshot upload/view."
                    ),
                )

    if _supabase_client is None:
        supabase_url, service_key = _get_storage_credentials()
        try:
            _supabase_client = create_client(supabase_url, service_key)
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Supabase storage key is incompatible with the Python SDK. "
                    "Provide a JWT-format service role key or use REST fallback mode."
                ),
            ) from exc
    return _supabase_client


def _get_bucket_name() -> str:
    return (os.getenv("SUPABASE_SCREENSHOT_BUCKET") or "earnings").strip() or "earnings"


def _extract_signed_url(value: Any) -> Optional[str]:
    if isinstance(value, dict):
        return value.get("signedURL") or value.get("signedUrl") or value.get("signed_url")

    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return data.get("signedURL") or data.get("signedUrl") or data.get("signed_url")

    return None


def _to_absolute_signed_url(signed_url: str) -> str:
    if signed_url.startswith("http://") or signed_url.startswith("https://"):
        return signed_url

    supabase_url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    if signed_url.startswith("/") and supabase_url:
        return f"{supabase_url}/storage/v1{signed_url}"

    return signed_url


async def _upload_to_storage_via_rest(
    *,
    supabase_url: str,
    service_key: str,
    bucket: str,
    storage_path: str,
    content: bytes,
    content_type: str,
) -> None:
    encoded_bucket = quote(bucket, safe="")
    encoded_path = quote(storage_path, safe="/")
    endpoint = f"{supabase_url}/storage/v1/object/{encoded_bucket}/{encoded_path}"

    headers = _storage_headers(service_key, content_type)
    headers["x-upsert"] = "false"

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(endpoint, headers=headers, content=content)

    if response.status_code not in {200, 201}:
        detail = _response_detail(response)
        raise HTTPException(status_code=502, detail=f"Failed to upload to storage: {detail}")


async def _create_signed_url_via_rest(
    *,
    supabase_url: str,
    service_key: str,
    bucket: str,
    storage_path: str,
    expires_in: int,
) -> str:
    encoded_bucket = quote(bucket, safe="")
    encoded_path = quote(storage_path, safe="/")
    endpoint = f"{supabase_url}/storage/v1/object/sign/{encoded_bucket}/{encoded_path}"

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            endpoint,
            headers=_storage_headers(service_key, "application/json"),
            json={"expiresIn": expires_in},
        )

    if response.status_code not in {200, 201}:
        detail = _response_detail(response)
        raise HTTPException(status_code=502, detail=f"Could not generate access link: {detail}")

    payload = response.json()
    signed_url = _extract_signed_url(payload)
    if not signed_url:
        raise HTTPException(status_code=502, detail="Could not generate access link")

    return _to_absolute_signed_url(signed_url)


async def _upload_to_storage(storage_path: str, content: bytes, content_type: str) -> None:
    bucket = _get_bucket_name()
    supabase_url, service_key = _get_storage_credentials()

    if _is_sdk_compatible_key(service_key):
        try:
            storage = get_supabase_client().storage.from_(bucket)
            storage.upload(
                storage_path,
                content,
                {"content-type": content_type},
            )
            return
        except HTTPException:
            pass
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Failed to upload to storage") from exc

    await _upload_to_storage_via_rest(
        supabase_url=supabase_url,
        service_key=service_key,
        bucket=bucket,
        storage_path=storage_path,
        content=content,
        content_type=content_type,
    )


async def _create_signed_url(storage_path: str, expires_in: int) -> str:
    bucket = _get_bucket_name()
    supabase_url, service_key = _get_storage_credentials()

    if _is_sdk_compatible_key(service_key):
        try:
            storage = get_supabase_client().storage.from_(bucket)
            signed_result = storage.create_signed_url(storage_path, expires_in)
            signed_url = _extract_signed_url(signed_result)
            if not signed_url:
                raise HTTPException(status_code=502, detail="Could not generate access link")
            return _to_absolute_signed_url(signed_url)
        except HTTPException:
            pass
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Could not generate access link: {exc}") from exc

    return await _create_signed_url_via_rest(
        supabase_url=supabase_url,
        service_key=service_key,
        bucket=bucket,
        storage_path=storage_path,
        expires_in=expires_in,
    )


def _to_json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def _serialize_record(record: Any) -> dict:
    return {key: _to_json_value(record[key]) for key in record.keys()}


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

    await _upload_to_storage(
        storage_path,
        content,
        file.content_type or "application/octet-stream",
    )

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
            s.hours_worked,
            s.gross_earned,
            s.platform_deductions,
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

    previews_enabled = True
    try:
        _get_storage_credentials()
    except HTTPException:
        previews_enabled = False

    result = []
    for row in rows:
        item = _serialize_record(row)
        item["signed_preview_url"] = None

        storage_path = str(item.get("storage_path") or "").strip()
        if previews_enabled and storage_path:
            try:
                item["signed_preview_url"] = await _create_signed_url(storage_path, 300)
            except Exception:
                item["signed_preview_url"] = None

        result.append(item)

    return result


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

    expires_in = 60
    bucket = _get_bucket_name()
    signed_url = await _create_signed_url(str(screenshot["storage_path"]), expires_in)

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