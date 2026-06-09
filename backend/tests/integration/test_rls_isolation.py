"""Proves Row-Level Security is actually enforced now that the app connects as
the non-owner app_user role. Without tenant context, users rows are invisible;
with context, only that tenant's rows are visible."""
from __future__ import annotations

import asyncpg
import pytest

from app.config import settings
from tests.integration.conftest import _db_reachable

pytestmark = pytest.mark.skipif(not _db_reachable(), reason="Postgres not reachable on localhost:5433")

DEFAULT_TENANT = settings.default_tenant_id


def _dsn() -> str:
    url = settings.database_url
    return "postgresql://" + url[len("postgres://"):] if url.startswith("postgres://") else url


async def test_app_user_is_not_rls_bypassing() -> None:
    conn = await asyncpg.connect(dsn=_dsn())
    try:
        bypass = await conn.fetchval(
            "SELECT rolbypassrls FROM pg_roles WHERE rolname = current_user"
        )
        assert bypass is False, "app role must not bypass RLS"
    finally:
        await conn.close()


async def test_users_invisible_without_tenant_context() -> None:
    conn = await asyncpg.connect(dsn=_dsn())
    try:
        # No app.current_tenant_id set -> policy fails closed -> zero rows.
        count = await conn.fetchval("SELECT count(*) FROM users")
        assert count == 0
    finally:
        await conn.close()


async def test_users_scoped_to_tenant_with_context() -> None:
    conn = await asyncpg.connect(dsn=_dsn())
    try:
        async with conn.transaction():
            await conn.execute("SELECT set_config('app.current_tenant_id', $1, true)", DEFAULT_TENANT)
            rows = await conn.fetch("SELECT tenant_id FROM users")
            # Every visible row belongs to the active tenant (isolation holds).
            assert all(str(r["tenant_id"]) == DEFAULT_TENANT for r in rows)
    finally:
        await conn.close()
