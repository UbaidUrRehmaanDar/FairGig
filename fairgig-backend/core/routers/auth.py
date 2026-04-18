from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth_middleware import get_current_user

router = APIRouter()


class ProfileSetupIn(BaseModel):
    full_name: str
    city_zone: str
    platform_category: str
    role: str


@router.post("/setup-profile")
async def setup_profile(profile: ProfileSetupIn, user=Depends(get_current_user)):
    return {
        "id": user["id"],
        "status": "skeleton",
        "profile": profile.dict(),
    }
