from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from auth_middleware import get_current_user, require_role

router = APIRouter()


@router.post("/upload/{shift_id}")
async def upload_screenshot(
    shift_id: str,
    file: UploadFile = File(...),
    user=Depends(require_role("worker")),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required")

    return {
        "status": "uploaded",
        "shift_id": shift_id,
        "filename": file.filename,
        "worker_id": user["id"],
    }


@router.get("/pending")
async def pending_screenshots(user=Depends(require_role("verifier", "advocate"))):
    return []


@router.patch("/{screenshot_id}/review")
async def review_screenshot(
    screenshot_id: str,
    status: str,
    note: str = "",
    user=Depends(require_role("verifier", "advocate")),
):
    if status not in ("verified", "flagged", "unverifiable"):
        raise HTTPException(status_code=400, detail="Invalid status")

    return {
        "status": "updated",
        "screenshot_id": screenshot_id,
        "review_status": status,
        "note": note,
        "reviewed_by": user["id"],
    }
