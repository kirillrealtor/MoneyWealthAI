"""Durable Plaid-sync queue (migration 010 + worker): proves enqueue is
idempotent, jobs are claimed atomically and processed off the request path, and
crash-orphaned jobs are recovered."""
from __future__ import annotations

import asyncio
import time

import httpx
import pytest

import app.modules.plaid.sync as syncmod
from app import db
from app.config import settings
from app.encryption import encrypt
from app.modules.plaid import worker
from tests.integration.auth_helpers import create_user_via_magic_link
from tests.integration.conftest import _db_reachable
from tests.integration.test_plaid_sync import _make_fake_plaid

pytestmark = pytest.mark.skipif(not _db_reachable(), reason="Postgres not reachable on localhost:5433")
TENANT = settings.default_tenant_id


async def _seed_item(client: httpx.AsyncClient) -> tuple[str, str, str]:
    email = f"queue+{int(time.time()*1_000_000)}@example.com"
    user_id, _ = await create_user_via_magic_link(client, email)
    account_pid = f"acc_{user_id}"
    token_enc = encrypt("access-sandbox-q", aad=user_id)
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
    return str(item_id), user_id, account_pid


async def test_enqueue_is_idempotent(client: httpx.AsyncClient) -> None:
    item_id, user_id, _ = await _seed_item(client)
    first = await worker.enqueue_sync(item_id, TENANT, user_id)
    second = await worker.enqueue_sync(item_id, TENANT, user_id)  # already outstanding
    assert first is not None
    assert second is None  # coalesced, not a second job

    async with db.with_tenant(TENANT) as conn:
        pending = await conn.fetchval(
            "SELECT count(*) FROM sync_jobs WHERE item_id = $1 AND status = 'pending'", item_id
        )
    assert pending == 1


async def test_concurrent_enqueue_coalesces_to_one_job(client: httpx.AsyncClient) -> None:
    """The partial unique index (migration 011) makes idempotency a hard
    guarantee: 20 concurrent enqueues for one item yield exactly one pending job,
    even if several race past the WHERE-NOT-EXISTS check."""
    item_id, user_id, _ = await _seed_item(client)
    results = await asyncio.gather(*(worker.enqueue_sync(item_id, TENANT, user_id) for _ in range(20)))

    created = [r for r in results if r is not None]
    assert len(created) == 1  # exactly one winner; the rest coalesced to None

    async with db.with_tenant(TENANT) as conn:
        pending = await conn.fetchval(
            "SELECT count(*) FROM sync_jobs WHERE item_id = $1 AND status = 'pending'", item_id
        )
    assert pending == 1


async def test_claim_and_process_completes_job(client: httpx.AsyncClient, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    item_id, user_id, account_pid = await _seed_item(client)
    monkeypatch.setattr(syncmod, "get_plaid", lambda *a, **kw: _make_fake_plaid(account_pid))
    await worker.enqueue_sync(item_id, TENANT, user_id)

    claimed = await worker._claim(10)
    mine = [j for j in claimed if str(j["item_id"]) == item_id]
    assert len(mine) == 1  # claimed exactly once

    sem = asyncio.Semaphore(5)
    await worker.process_job(mine[0], sem)

    async with db.with_tenant(TENANT) as conn:
        row = await conn.fetchrow(
            "SELECT status, transactions_synced FROM sync_jobs WHERE sync_id = $1", str(mine[0]["sync_id"])
        )
        tx = await conn.fetchval(
            """SELECT count(*) FROM transactions
                WHERE account_id IN (SELECT account_id FROM plaid_accounts WHERE item_id = $1)""",
            item_id,
        )
    assert row["status"] == "completed"
    assert row["transactions_synced"] == 2
    assert tx == 2


async def test_recovery_requeues_orphaned_running_job(client: httpx.AsyncClient) -> None:
    """A job stuck 'running' (worker crashed mid-flight) is requeued by the
    recovery sweep once it's older than the stale threshold."""
    item_id, user_id, _ = await _seed_item(client)
    async with db.with_tenant(TENANT) as conn:
        sync_id = await conn.fetchval(
            """INSERT INTO sync_jobs (item_id, tenant_id, user_id, status, started_at)
               VALUES ($1,$2,$3,'running', NOW() - INTERVAL '1 hour') RETURNING sync_id""",
            item_id, TENANT, user_id,
        )

    recovered = await db.fetchval("SELECT recover_stale_sync_jobs($1, $2)", 900, 5)
    assert int(recovered) >= 1

    async with db.with_tenant(TENANT) as conn:
        row = await conn.fetchrow("SELECT status, retry_count FROM sync_jobs WHERE sync_id = $1", str(sync_id))
    assert row["status"] == "pending"   # requeued, not lost
    assert row["retry_count"] == 1
