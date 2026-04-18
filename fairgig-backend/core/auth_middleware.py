import os
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env")

security = HTTPBearer(auto_error=False)
ALGORITHM = (os.getenv("JWT_ALGORITHM") or "HS256").strip() or "HS256"


def _get_jwt_secret() -> str:
    return (os.getenv("SUPABASE_JWT_SECRET") or "").strip()


def _resolve_role(user_metadata: Any, app_metadata: Any) -> str:
    if isinstance(user_metadata, dict) and isinstance(user_metadata.get("role"), str):
        return user_metadata["role"]
    if isinstance(app_metadata, dict) and isinstance(app_metadata.get("role"), str):
        return app_metadata["role"]
    return "worker"


async def _verify_token_with_supabase(token: str) -> Optional[dict]:
    supabase_url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    service_key = (
        os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or ""
    ).strip()
    if not supabase_url or not service_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                f"{supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": service_key,
                },
            )
    except Exception:
        return None

    if response.status_code != 200:
        return None

    payload = response.json()
    user_id = payload.get("id")
    if not isinstance(user_id, str) or not user_id.strip():
        return None

    role = _resolve_role(payload.get("user_metadata"), payload.get("app_metadata"))
    return {"id": user_id, "role": role}


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = credentials.credentials.strip()

    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    payload = None
    jwt_secret = _get_jwt_secret()
    if jwt_secret:
        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=[ALGORITHM],
                options={
                    "verify_aud": False,
                },
            )
        except JWTError:
            payload = None

    if payload is None:
        fallback_user = await _verify_token_with_supabase(token)
        if fallback_user is None:
            raise HTTPException(status_code=401, detail="Token invalid or expired")
        return fallback_user

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(status_code=401, detail="Invalid token")

    role = _resolve_role(payload.get("user_metadata"), payload.get("app_metadata"))

    return {"id": user_id, "role": role}


def require_role(*roles):
    async def checker(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return checker
