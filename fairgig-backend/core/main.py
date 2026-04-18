import os
from contextlib import asynccontextmanager
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import close_pool, get_pool
from routers import analytics, auth, certificates, grievances, screenshots, shifts


load_dotenv()


def _parse_allowed_origins(raw: str, fallback: List[str]) -> List[str]:
    if not raw:
        return fallback
    parsed = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return parsed or fallback


def _is_truthy(value: str) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


DEFAULT_ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]
ALLOWED_ORIGINS = _parse_allowed_origins(
    os.getenv("CORE_ALLOWED_ORIGINS", ""),
    DEFAULT_ALLOWED_ORIGINS,
)
STRICT_STARTUP = _is_truthy(os.getenv("STRICT_STARTUP", "false"))
ENVIRONMENT = (os.getenv("ENVIRONMENT") or "development").strip().lower()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail hard in production-like environments if dependencies are unavailable.
    try:
        await get_pool()
    except Exception:
        if STRICT_STARTUP or ENVIRONMENT in {"production", "staging"}:
            raise
    yield
    try:
        await close_pool()
    except Exception:
        pass


app = FastAPI(title="FairGig Core API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(shifts.router, prefix="/shifts", tags=["shifts"])
app.include_router(screenshots.router, prefix="/screenshots", tags=["screenshots"])
app.include_router(grievances.router, prefix="/grievances", tags=["grievances"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(certificates.router, prefix="/certificates", tags=["certificates"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "fairgig-core"}
