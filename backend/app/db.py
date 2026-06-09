"""Database access layer (asyncpg).

A single shared pool. In production the connection string points at RDS Proxy,
which multiplexes these onto a small set of real Aurora connections - this is
what lets the agentic AI loop hold "connections" without exhausting Aurora
(Architecture 2). Queries use $1, $2 placeholders (asyncpg native); never
string-interpolate user input.
"""
from __future__ import annotations

import time
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any, cast

import asyncpg

from app.config import settings
from app.logging_conf import logger

_pool: asyncpg.Pool | None = None


def _normalize_dsn(url: str) -> str:
    # asyncpg wants postgresql:// ; accept the common postgres:// alias too.
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


async def init_pool() -> None:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=_normalize_dsn(settings.database_url),
            min_size=2,
            max_size=10,  # per-instance; RDS Proxy fans these out safely
            command_timeout=10,
        )
        logger.info("db pool initialized", service="database")


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def _require_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized; call init_pool() at startup")
    return _pool


async def execute(sql: str, *params: Any) -> str:
    start = time.monotonic()
    try:
        result = await _require_pool().execute(sql, *params)
        logger.debug("db execute", service="database", latency_ms=_ms(start))
        return cast(str, result)
    except Exception as err:  # noqa: BLE001 - logged and re-raised
        logger.error("db execute failed", service="database", error_type="DB_QUERY_FAILED", error_message=str(err))
        raise


async def fetch(sql: str, *params: Any) -> list[asyncpg.Record]:
    start = time.monotonic()
    try:
        rows = await _require_pool().fetch(sql, *params)
        logger.debug("db fetch", service="database", latency_ms=_ms(start), rows=len(rows))
        return cast("list[asyncpg.Record]", rows)
    except Exception as err:  # noqa: BLE001
        logger.error("db fetch failed", service="database", error_type="DB_QUERY_FAILED", error_message=str(err))
        raise


async def fetchrow(sql: str, *params: Any) -> asyncpg.Record | None:
    start = time.monotonic()
    try:
        row = await _require_pool().fetchrow(sql, *params)
        logger.debug("db fetchrow", service="database", latency_ms=_ms(start))
        return row
    except Exception as err:  # noqa: BLE001
        logger.error("db fetchrow failed", service="database", error_type="DB_QUERY_FAILED", error_message=str(err))
        raise


async def fetchval(sql: str, *params: Any) -> Any:
    return await _require_pool().fetchval(sql, *params)


@asynccontextmanager
async def with_tenant(tenant_id: str) -> AsyncIterator[asyncpg.Connection]:
    """Yield a connection inside a transaction with the tenant context set, so
    Row-Level Security policies apply (Architecture 6 / schema RLS). The
    set_config(..., true) makes it transaction-local - safe with pooling.
    """
    pool = _require_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("SELECT set_config('app.current_tenant_id', $1, true)", tenant_id)
            yield conn


def _ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)


__all__ = [
    "init_pool",
    "close_pool",
    "execute",
    "fetch",
    "fetchrow",
    "fetchval",
    "with_tenant",
    "Sequence",
]
