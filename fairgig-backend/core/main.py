import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import close_pool, get_pool
from routers import analytics, auth, certificates, screenshots, shifts


BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env")


def _parse_origin_list(raw: str) -> List[str]:
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]


def _parse_allowed_origins(raw: str, fallback: List[str]) -> List[str]:
    merged = {origin.strip().rstrip("/") for origin in fallback if origin.strip()}
    merged.update(_parse_origin_list(raw))
    return sorted(merged)


def _is_truthy(value: str) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3005",
    "http://localhost:3006",
    "http://localhost:3007",
    "http://localhost:3015",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "http://127.0.0.1:3005",
    "http://127.0.0.1:3006",
    "http://127.0.0.1:3007",
    "http://127.0.0.1:3015",
]
DEFAULT_ALLOWED_ORIGINS.extend(_parse_origin_list(os.getenv("FRONTEND_URL", "")))
DEFAULT_ALLOWED_ORIGINS.extend(_parse_origin_list(os.getenv("VERCEL_FRONTEND_URL", "")))
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(shifts.router, prefix="/shifts", tags=["shifts"])
app.include_router(screenshots.router, prefix="/screenshots", tags=["screenshots"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(certificates.router, prefix="/certificates", tags=["certificates"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "fairgig-core"}
