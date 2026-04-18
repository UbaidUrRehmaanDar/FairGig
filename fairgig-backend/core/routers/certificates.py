from datetime import date

from fastapi import APIRouter, Depends

from auth_middleware import get_current_user

router = APIRouter()


@router.get("/data")
async def certificate_data(
    start_date: date,
    end_date: date,
    user=Depends(get_current_user),
):
    return {
        "worker": {"id": user["id"]},
        "period": {"start": str(start_date), "end": str(end_date)},
        "shifts": [],
        "summary": {
            "total_gross": 0,
            "total_net": 0,
            "total_shifts": 0,
            "total_hours": 0,
        },
    }
