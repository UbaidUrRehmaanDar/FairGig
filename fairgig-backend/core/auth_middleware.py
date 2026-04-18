import os

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

load_dotenv()

security = HTTPBearer(auto_error=True)
ALGORITHM = (os.getenv("JWT_ALGORITHM") or "HS256").strip() or "HS256"


def _get_required_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise HTTPException(status_code=500, detail=f"{name} is not configured")
    return value


def _extract_role(payload: dict) -> str:
    app_metadata = payload.get("app_metadata")
    user_metadata = payload.get("user_metadata")

    if isinstance(app_metadata, dict):
        role = app_metadata.get("role")
        if isinstance(role, str) and role.strip():
            return role

    if isinstance(user_metadata, dict):
        role = user_metadata.get("role")
        if isinstance(role, str) and role.strip():
            return role

    return "worker"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials.strip()

    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    jwt_secret = _get_required_env("SUPABASE_JWT_SECRET")

    try:
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=[ALGORITHM],
            options={
                "verify_aud": False,
                "require_sub": True,
                "require_exp": True,
            },
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token invalid or expired") from exc

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(status_code=401, detail="Invalid token")

    role = _extract_role(payload)

    return {"id": user_id, "role": role}


def require_role(*roles):
    async def checker(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return checker
