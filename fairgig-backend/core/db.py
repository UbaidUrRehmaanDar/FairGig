import os
from typing import Optional

import asyncpg
from dotenv import load_dotenv

load_dotenv()

_pool: Optional[asyncpg.Pool] = None


def _require_database_url() -> str:
    database_url = (os.getenv("DATABASE_URL") or "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    return database_url


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
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


async def connect_to_db() -> asyncpg.Pool:
    return await get_pool()


async def close_db_connection(pool: Optional[asyncpg.Pool]) -> None:
    if pool is not None and pool is not _pool:
        await pool.close()
        return
    await close_pool()
