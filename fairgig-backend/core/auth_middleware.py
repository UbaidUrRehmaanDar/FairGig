import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

load_dotenv()

security = HTTPBearer(auto_error=False)
ALGORITHM = "HS256"


def _get_jwt_secret() -> str:
    secret = (os.getenv("SUPABASE_JWT_SECRET") or "").strip()
    if not secret:
        raise HTTPException(status_code=500, detail="JWT secret not configured")
    return secret


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = credentials.credentials.strip()

    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    try:
        payload = jwt.decode(
            token,
            _get_jwt_secret(),
            algorithms=[ALGORITHM],
            options={
                "verify_aud": False,
            },
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token invalid or expired") from exc

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(status_code=401, detail="Invalid token")

    user_metadata = payload.get("user_metadata")
    app_metadata = payload.get("app_metadata")

    role = "worker"
    if isinstance(user_metadata, dict) and isinstance(user_metadata.get("role"), str):
        role = user_metadata["role"]
    elif isinstance(app_metadata, dict) and isinstance(app_metadata.get("role"), str):
        role = app_metadata["role"]

    return {"id": user_id, "role": role}


def require_role(*roles):
    async def checker(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return checker
