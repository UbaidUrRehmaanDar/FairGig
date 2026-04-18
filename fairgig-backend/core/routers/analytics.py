from fastapi import APIRouter, Depends

from auth_middleware import require_role

router = APIRouter()


@router.get("/kpis")
async def kpis(user=Depends(require_role("advocate"))):
    return {
        "commission_trends": [],
        "income_by_zone": [],
        "vulnerability_flags": [],
        "top_complaints": [],
    }
