"""Proves the transaction sync is idempotent with a mocked Plaid client and a
real SQLite + Redis (RLS-scoped writes, cursor advance, ON CONFLICT)."""
from __future__ import annotations

import time

import httpx
import pytest

import app.modules.plaid.sync as syncmod
from app import db
from app.config import settings
from app.encryption import encrypt
from app.modules.plaid.sync import run_sync_for_item
from tests.integration.conftest import _db_reachable

pytestmark = pytest.mark.skipif(not _db_reachable(), reason="SQLite is always reachable")

TENANT = settings.default_tenant_id


def _make_fake_plaid(account_pid: str) -> object:
    page = {
        "added": [
            {
                "transaction_id": f"{account_pid}-tx1", "account_id": account_pid, "amount": 12.5,
                "date": "2026-06-01", "name": "Coffee",
                "personal_finance_category": {"primary": "FOOD", "detailed": "FOOD_COFFEE"},
                "pending": False, "iso_currency_code": "USD",
            },
            {
                "transaction_id": f"{account_pid}-tx2", "account_id": account_pid, "amount": 99.0,
                "date": "2026-06-02", "name": "Groceries",
                "personal_finance_category": {"primary": "FOOD", "detailed": "FOOD_GROCERIES"},
                "pending": False,
            },
        ],
        "modified": [], "removed": [], "has_more": False, "next_cursor": "cursor_end",
    }

    class _FakePlaid:
        async def transactions_sync(self, token: str, cursor: str | None, count: int = 500):  # type: ignore[no-untyped-def]
            if cursor is None:
                return page
            return {"added": [], "modified": [], "removed": [], "has_more": False, "next_cursor": cursor}

    return _FakePlaid()


async def test_transaction_sync_is_idempotent(client: httpx.AsyncClient, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    email = f"plaidsync+{int(time.time()*1000)}@example.com"
    r = await client.post("/api/v1/auth/signup", json={"email": email, "password": "SecurePass123!"})
    user_id = r.json()["user_id"]
    account_pid = f"acc_{user_id}"  # globally unique per test run

    token_enc = encrypt("access-sandbox-abc", aad=user_id)
    async with db.with_tenant(TENANT) as conn:
        item_id = await conn.fetchval(
            """INSERT INTO plaid_items (user_id, tenant_id, plaid_item_id, access_token_enc, item_status)
               VALUES ($1,$2,$3,$4,'good') RETURNING item_id""",
            user_id, TENANT, f"plaiditem_{user_id}", token_enc,
        )
        await conn.execute(
            """INSERT INTO plaid_accounts (item_id, tenant_id, plaid_account_id, name, type, subtype, currency_code)
               VALUES ($1,$2,$3,'Checking','depository','checking','USD')""",
            item_id, TENANT, account_pid,
        )

    monkeypatch.setattr(syncmod, "get_plaid", lambda: _make_fake_plaid(account_pid))

    n1 = await run_sync_for_item(str(item_id), TENANT, user_id)
    n2 = await run_sync_for_item(str(item_id), TENANT, user_id)

    async with db.with_tenant(TENANT) as conn:
        count = await conn.fetchval(
            """SELECT count(*) FROM transactions
                WHERE account_id IN (SELECT account_id FROM plaid_accounts WHERE item_id = $1)""",
            item_id,
        )

    assert n1 == 2          # first run ingests both transactions
    assert n2 == 0          # second run: cursor advanced, nothing new
    assert count == 2       # no duplicates despite re-running
