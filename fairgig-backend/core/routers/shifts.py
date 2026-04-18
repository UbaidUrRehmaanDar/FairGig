from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth_middleware import get_current_user, require_role

router = APIRouter()


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
    return {
        "shift_id": "skeleton-shift-id",
        "status": "logged",
        "worker_id": user["id"],
        "payload": shift.dict(),
    }


@router.get("/")
async def list_shifts(user=Depends(get_current_user)):
    return []


@router.get("/summary")
async def shift_summary(user=Depends(require_role("worker"))):
    return {
        "this_month": 0,
        "this_week": 0,
        "avg_hourly": 0,
        "avg_commission_pct": 0,
        "total_shifts": 0,
    }


@router.get("/city-median")
async def city_median(platform: str, user=Depends(require_role("worker"))):
    return {
        "platform": platform,
        "median_hourly": None,
        "median_daily": None,
        "note": "Skeleton response. Wire to city_medians materialized view.",
    }
