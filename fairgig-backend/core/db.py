from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

try:
    import asyncpg  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    asyncpg = None
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_ROOT / ".env")

_pool: Optional[Any] = None


def _require_database_url() -> str:
    database_url = (os.getenv("DATABASE_URL") or "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    return database_url


async def get_pool() -> Any:
    global _pool
    if _pool is None:
        if asyncpg is None:
            raise RuntimeError(
                "Database driver 'asyncpg' is not installed. "
                "Install fairgig-backend/core/requirements.txt to enable DB access."
            )
        _pool = await asyncpg.create_pool(
            _require_database_url(),
            min_size=2,
            max_size=10,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def connect_to_db() -> Any:
    return await get_pool()


async def close_db_connection(pool: Optional[Any]) -> None:
    if pool is not None and pool is not _pool:
        await pool.close()
        return
    await close_pool()
