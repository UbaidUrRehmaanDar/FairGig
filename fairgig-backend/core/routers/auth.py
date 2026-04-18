from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth_middleware import get_current_user
from db import get_pool

try:
    import asyncpg  # type: ignore
    ForeignKeyViolationError = asyncpg.ForeignKeyViolationError
except ModuleNotFoundError:  # pragma: no cover
    asyncpg = None

    class ForeignKeyViolationError(Exception):
        pass

router = APIRouter()


class ProfileSetupIn(BaseModel):
    full_name: str
    city_zone: str
    platform_category: str
    role: Literal["worker", "verifier", "advocate"]


@router.post("/setup-profile")
async def setup_profile(profile: ProfileSetupIn, user=Depends(get_current_user)):
    try:
        pool = await get_pool()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable.") from exc

    trusted_role = user.get("role") if isinstance(user.get("role"), str) else "worker"
    trusted_role = trusted_role.strip().lower() or "worker"

    try:
        row = await pool.fetchrow(
            """
            INSERT INTO profiles (id, full_name, city_zone, platform_category, role)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id)
            DO UPDATE SET
              full_name = EXCLUDED.full_name,
              city_zone = EXCLUDED.city_zone,
              platform_category = EXCLUDED.platform_category,
              role = EXCLUDED.role
            RETURNING id, role
            """,
            user["id"],
            profile.full_name,
            profile.city_zone,
            profile.platform_category,
            trusted_role,
        )
    except ForeignKeyViolationError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "User is not present in Supabase auth.users. "
                "Sign in through Supabase Auth first, then retry setup-profile."
            ),
        ) from exc

    return {
        "id": str(row["id"]),
        "role": row["role"],
        "status": "profile_saved",
    }
