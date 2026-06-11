"""Database access layer (aiosqlite).

Provides a PostgreSQL-compatible query wrapper and connection pool on top of SQLite,
mapping placeholders, functions, and standard constraints.
"""
from __future__ import annotations

import asyncio
import datetime
import os
import re
import sqlite3
import time
import uuid
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any, cast

import aiosqlite

from app.config import settings
from app.errors import ApiError
from app.logging_conf import logger

import decimal
UniqueViolationError = sqlite3.IntegrityError
sqlite3.register_adapter(decimal.Decimal, lambda d: float(d))


_pool: SQLiteConnectionPool | None = None
_POOL_ACQUIRE_TIMEOUT = 5.0


def sqlite_now() -> str:
    """Return UTC timestamp in format matching SQLite's CURRENT_TIMESTAMP."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def sqlite_date_trunc(unit: str, val: Any) -> str:
    """Truncate datetime values to start of month/year/day in SQLite."""
    if val is None:
        return ""
    if isinstance(val, (datetime.datetime, datetime.date)):
        y, m, d = val.year, val.month, val.day
    else:
        val_str = str(val)
        date_str = val_str.split("T")[0].split(" ")[0]
        parts = date_str.split("-")
        if len(parts) >= 3:
            try:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            except ValueError:
                return val_str
        else:
            return val_str

    if unit == "month":
        return f"{y:04d}-{m:02d}-01"
    elif unit == "year":
        return f"{y:04d}-01-01"
    elif unit == "day":
        return f"{y:04d}-{m:02d}-{d:02d}"
    return f"{y:04d}-{m:02d}-{d:02d}"


def sqlite_to_char(val: Any, format_str: str) -> str:
    """Format dates to match Postgres date string format."""
    if val is None:
        return ""
    val_str = str(val)
    date_str = val_str.split("T")[0].split(" ")[0]
    parts = date_str.split("-")
    if len(parts) >= 3:
        y, m, d = parts[0], parts[1], parts[2]
        if format_str == "YYYY-MM":
            return f"{y}-{m}"
        elif format_str == "YYYY_MM":
            return f"{y}_{m}"
    return val_str


def sqlite_gen_random_uuid() -> str:
    """Generate a random UUID v4 string."""
    return str(uuid.uuid4())


def translate_postgres_to_sqlite(sql: str) -> str:
    """Translates common Postgres-specific query patterns to standard SQLite."""
    # Strip type casts on placeholders (e.g. $2::text[], $1::uuid)
    sql = re.sub(r"::[a-zA-Z_\[\]]+", "", sql)

    # 1. date_trunc('month', CURRENT_DATE) - INTERVAL 'X months' -> date(date_trunc('month', date('now')), '-X months')
    sql = re.sub(
        r"date_trunc\('month',\s*CURRENT_DATE\)\s*-\s*INTERVAL\s*'(\d+)\s*month(s)?'",
        r"date(date_trunc('month', date('now')), '-\1 months')",
        sql,
        flags=re.IGNORECASE,
    )

    # 2. CURRENT_DATE - INTERVAL 'X days' -> date('now', '-X days')
    sql = re.sub(
        r"CURRENT_DATE\s*-\s*INTERVAL\s*'(\d+)\s*day(s)?'",
        r"date('now', '-\1 days')",
        sql,
        flags=re.IGNORECASE,
    )

    # 3. date_trunc('month', ANY) - INTERVAL 'X months'
    sql = re.sub(
        r"date_trunc\('month',\s*([^)]+)\)\s*-\s*INTERVAL\s*'(\d+)\s*month(s)?'",
        r"date(date_trunc('month', \1), '-\2 months')",
        sql,
        flags=re.IGNORECASE,
    )

    # 4. Map CURRENT_DATE to SQLite date('now')
    sql = re.sub(r"\bCURRENT_DATE\b", "date('now')", sql, flags=re.IGNORECASE)

    # 5. Translate Postgres <> ALL(ARRAY[...]) array checks
    sql = re.sub(
        r"<>\s*ALL\(ARRAY\['TRANSFER','TRANSFER_IN','TRANSFER_OUT','LOAN_PAYMENTS'\]\)",
        r"NOT IN ('TRANSFER','TRANSFER_IN','TRANSFER_OUT','LOAN_PAYMENTS')",
        sql,
        flags=re.IGNORECASE,
    )

    return sql


def _prepare_query(sql: str, params: Sequence[Any]) -> tuple[str, list[Any]]:
    """Transforms PostgreSQL placeholders and queries to SQLite-compatible equivalents."""
    sql_translated = translate_postgres_to_sqlite(sql)
    placeholders = re.findall(r"\$(\d+)", sql_translated)
    if not placeholders:
        return sql_translated, list(params)

    new_params = []

    def replace_match(match: re.Match[str]) -> str:
        idx = int(match.group(1)) - 1
        if idx < len(params):
            new_params.append(params[idx])
        else:
            new_params.append(None)
        return "?"

    new_sql = re.sub(r"\$(\d+)", replace_match, sql_translated)
    return new_sql, new_params


class SQLiteConnectionPool:
    """Async connection pool for SQLite to replicate asyncpg pool structure."""

    def __init__(self, db_path: str, min_size: int = 2, max_size: int = 10):
        self.db_path = db_path
        self.min_size = min_size
        self.max_size = max_size
        self._queue: asyncio.Queue[aiosqlite.Connection] = asyncio.Queue(max_size)
        self._allocated = 0
        self._lock = asyncio.Lock()

    async def init(self) -> None:
        # Resolve path relative to backend root if it's a relative path and doesn't exist
        db_file = self.db_path
        if db_file != ":memory:" and not os.path.isabs(db_file):
            # Resolve relative to workspace backend folder
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_file = os.path.join(backend_dir, db_file)
            # Ensure directories exist
            os.makedirs(os.path.dirname(db_file), exist_ok=True)
            self.db_path = db_file

        for _ in range(self.min_size):
            conn = await self._create_connection()
            await self._queue.put(conn)
            self._allocated += 1

    async def _create_connection(self) -> aiosqlite.Connection:
        conn = await aiosqlite.connect(self.db_path, check_same_thread=False, isolation_level=None)
        conn.row_factory = sqlite3.Row
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.execute("PRAGMA foreign_keys=ON;")
        # Register PostgreSQL custom functions equivalents
        await conn.create_function("now", 0, sqlite_now)
        await conn.create_function("date_trunc", 2, sqlite_date_trunc)
        await conn.create_function("to_char", 2, sqlite_to_char)
        await conn.create_function("gen_random_uuid", 0, sqlite_gen_random_uuid)
        return conn

    async def acquire(self, timeout: float = _POOL_ACQUIRE_TIMEOUT) -> aiosqlite.Connection:
        try:
            return await asyncio.wait_for(self._acquire_internal(), timeout=timeout)
        except asyncio.TimeoutError as err:
            raise TimeoutError("Timeout acquiring SQLite connection") from err

    async def _acquire_internal(self) -> aiosqlite.Connection:
        async with self._lock:
            if not self._queue.empty():
                return await self._queue.get()
            if self._allocated < self.max_size:
                conn = await self._create_connection()
                self._allocated += 1
                return conn
        return await self._queue.get()

    async def release(self, conn: aiosqlite.Connection) -> None:
        await self._queue.put(conn)

    async def close(self) -> None:
        async with self._lock:
            while not self._queue.empty():
                conn = await self._queue.get()
                await conn.close()
            self._allocated = 0


class SQLiteConnectionWrapper:
    """Wrapper that translates Postgres calls into SQLite standard executes."""

    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def execute(self, sql: str, *params: Any) -> str:
        sql_prepared, params_prepared = _prepare_query(sql, params)
        cursor = await self._conn.execute(sql_prepared, params_prepared)
        op = sql_prepared.strip().split()[0].upper()
        if op in ("UPDATE", "DELETE", "INSERT"):
            return f"{op} {cursor.rowcount}"
        return ""

    async def fetch(self, sql: str, *params: Any) -> list[sqlite3.Row]:
        sql_prepared, params_prepared = _prepare_query(sql, params)
        async with self._conn.execute(sql_prepared, params_prepared) as cursor:
            rows = await cursor.fetchall()
            return list(rows)

    async def fetchrow(self, sql: str, *params: Any) -> sqlite3.Row | None:
        sql_prepared, params_prepared = _prepare_query(sql, params)
        async with self._conn.execute(sql_prepared, params_prepared) as cursor:
            return await cursor.fetchone()

    async def fetchval(self, sql: str, *params: Any) -> Any:
        sql_prepared, params_prepared = _prepare_query(sql, params)
        async with self._conn.execute(sql_prepared, params_prepared) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

    async def commit(self) -> None:
        await self._conn.commit()

    async def rollback(self) -> None:
        await self._conn.rollback()

    def transaction(self) -> SQLiteTransaction:
        return SQLiteTransaction(self._conn)


class SQLiteTransaction:
    """Transaction helper reproducing the asyncpg connection transaction protocol."""

    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def __aenter__(self) -> SQLiteTransaction:
        await self._conn.execute("BEGIN TRANSACTION;")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            await self._conn.rollback()
        else:
            await self._conn.commit()


async def init_pool() -> None:
    global _pool
    if _pool is None:
        db_path = settings.database_url
        if db_path.startswith("sqlite+aiosqlite:///"):
            db_path = db_path[len("sqlite+aiosqlite:///") :]
        elif db_path.startswith("sqlite:///"):
            db_path = db_path[len("sqlite:///") :]

        _pool = SQLiteConnectionPool(db_path=db_path, min_size=2, max_size=10)
        await _pool.init()
        logger.info("sqlite db pool initialized", service="database", path=db_path)


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def _require_pool() -> SQLiteConnectionPool:
    if _pool is None:
        raise RuntimeError("DB pool not initialized; call init_pool() at startup")
    return _pool


@asynccontextmanager
async def _acquire() -> AsyncIterator[SQLiteConnectionWrapper]:
    pool = _require_pool()
    try:
        conn = await pool.acquire(timeout=_POOL_ACQUIRE_TIMEOUT)
    except TimeoutError as err:
        logger.error("db pool acquire timeout", service="database", error_type="POOL_EXHAUSTED")
        raise ApiError("SERVICE_BUSY") from err
    try:
        yield SQLiteConnectionWrapper(conn)
    finally:
        await pool.release(conn)


async def execute(sql: str, *params: Any) -> str:
    start = time.monotonic()
    try:
        async with _acquire() as conn:
            result = await conn.execute(sql, *params)
        logger.debug("db execute", service="database", latency_ms=_ms(start))
        return result
    except ApiError:
        raise
    except Exception as err:
        logger.error("db execute failed", service="database", error_type="DB_QUERY_FAILED", error_message=str(err))
        raise


async def fetch(sql: str, *params: Any) -> list[sqlite3.Row]:
    start = time.monotonic()
    try:
        async with _acquire() as conn:
            rows = await conn.fetch(sql, *params)
        logger.debug("db fetch", service="database", latency_ms=_ms(start), rows=len(rows))
        return rows
    except ApiError:
        raise
    except Exception as err:
        logger.error("db fetch failed", service="database", error_type="DB_QUERY_FAILED", error_message=str(err))
        raise


async def fetchrow(sql: str, *params: Any) -> sqlite3.Row | None:
    start = time.monotonic()
    try:
        async with _acquire() as conn:
            row = await conn.fetchrow(sql, *params)
        logger.debug("db fetchrow", service="database", latency_ms=_ms(start))
        return row
    except ApiError:
        raise
    except Exception as err:
        logger.error("db fetchrow failed", service="database", error_type="DB_QUERY_FAILED", error_message=str(err))
        raise


async def fetchval(sql: str, *params: Any) -> Any:
    async with _acquire() as conn:
        return await conn.fetchval(sql, *params)


@asynccontextmanager
async def with_tenant(tenant_id: str) -> AsyncIterator[SQLiteConnectionWrapper]:
    """Yield a connection inside a transaction (RLS checks bypassed in SQLite)."""
    async with _acquire() as conn:
        async with SQLiteTransaction(conn._conn):
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
    "UniqueViolationError",
]
