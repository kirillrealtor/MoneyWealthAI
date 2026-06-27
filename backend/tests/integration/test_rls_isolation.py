"""Proves Row-Level Security is actually enforced now that the app connects as
the non-owner app_user role. Without tenant context, users rows are invisible;
with context, only that tenant's rows are visible."""
from __future__ import annotations

import time
from decimal import Decimal

import asyncpg
import httpx
import pytest

from app import db
from app.config import settings
from app.modules.budgets import service as budgets
from tests.integration.auth_helpers import create_user_via_magic_link
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


async def _signup(c: httpx.AsyncClient) -> str:
    email = f"rls+{int(time.time()*1_000_000)}@example.com"
    user_id, _ = await create_user_via_magic_link(c, email)
    return user_id


async def test_user_rls_backstop_hides_other_users_rows_in_same_tenant(client: httpx.AsyncClient) -> None:
    """Two users in the SAME tenant: with a user in context, the per-user RLS
    backstop (migration 009) hides the other user's rows even though the tenant
    matches — so a query that forgets `WHERE user_id` can't leak across users.
    Without a user in context, tenant RLS alone still shows both (proving the
    backstop is what's doing the user-level filtering)."""
    user_a = await _signup(client)
    user_b = await _signup(client)

    await budgets.create_budget(
        user_a, DEFAULT_TENANT, category="dining_a", monthly_limit=Decimal("100"), alert_at_pct=80)
    await budgets.create_budget(
        user_b, DEFAULT_TENANT, category="dining_b", monthly_limit=Decimal("100"), alert_at_pct=80)

    # With user A in context: a deliberately unscoped SELECT sees ONLY A's rows.
    async with db.with_tenant(DEFAULT_TENANT, user_a) as conn:
        cats = {r["category"] for r in await conn.fetch("SELECT category FROM budgets")}
    assert "dining_a" in cats
    assert "dining_b" not in cats  # backstop hid user B's row

    # Tenant-only context (no user): the same unscoped SELECT sees both, proving
    # the user GUC — not the tenant policy — is enforcing user isolation.
    async with db.with_tenant(DEFAULT_TENANT) as conn:
        cats_all = {r["category"] for r in await conn.fetch("SELECT category FROM budgets")}
    assert {"dining_a", "dining_b"} <= cats_all

    # WITH CHECK: user A cannot write a row owned by user B.
    with pytest.raises(asyncpg.PostgresError):
        async with db.with_tenant(DEFAULT_TENANT, user_a) as conn:
            await conn.execute(
                "INSERT INTO budgets (user_id, tenant_id, category, monthly_limit, alert_at_pct) "
                "VALUES ($1, $2, 'sneaky', 50, 80)",
                user_b, DEFAULT_TENANT,
            )
