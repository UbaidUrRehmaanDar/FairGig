from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth_middleware import get_current_user, require_role

router = APIRouter()


class GrievanceIn(BaseModel):
    platform: str
    category: str
    title: str
    description: str
    tags: Optional[List[str]] = []


@router.post("/")
async def create_grievance(g: GrievanceIn, user=Depends(require_role("worker"))):
    return {
        "id": "skeleton-grievance-id",
        "worker_id": user["id"],
        "payload": g.dict(),
    }


@router.get("/")
async def list_grievances(
    platform: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
):
    return {
        "items": [],
        "filters": {
            "platform": platform,
            "category": category,
            "status": status,
        },
    }


@router.patch("/{grievance_id}/escalate")
async def escalate(grievance_id: str, user=Depends(require_role("advocate"))):
    return {
        "status": "escalated",
        "grievance_id": grievance_id,
        "escalated_by": user["id"],
    }


@router.post("/{grievance_id}/upvote")
async def upvote(grievance_id: str, user=Depends(get_current_user)):
    return {
        "ok": True,
        "grievance_id": grievance_id,
        "user_id": user["id"],
    }
