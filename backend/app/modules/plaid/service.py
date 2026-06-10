"""Plaid business logic: link token, token exchange (encrypt + store), list,
disconnect. All DB access is tenant-scoped via db.with_tenant (RLS enforced).
Access tokens are encrypted at rest and only decrypted in-memory for API calls.
"""
from __future__ import annotations

import asyncio
from typing import Any

from app import db
from app.audit import audit
from app.encryption import decrypt, encrypt
from app.errors import ApiError
from app.integrations.plaid_client import get_plaid
from app.logging_conf import logger

from .sync import run_sync_for_item, sync_investments_for_item, sync_liabilities_for_item, to_money


async def create_link_token(user_id: str) -> dict[str, Any]:
    plaid = get_plaid()
    result = await plaid.create_link_token(user_id)
    await audit("plaid.link_token_created", user_id=user_id, resource="plaid_item")
    return {"link_token": result["link_token"], "expiration": result.get("expiration")}


async def exchange_public_token(user_id: str, tenant_id: str, public_token: str, ip: str | None) -> dict[str, Any]:
    plaid = get_plaid()

    # 1. Network calls first (outside any DB transaction — keep transactions short).
    exchanged = await plaid.exchange_public_token(public_token)
    access_token: str = exchanged["access_token"]
    plaid_item_id: str = exchanged["item_id"]

    item_info = await plaid.get_item(access_token)
    institution_id = (item_info.get("item") or {}).get("institution_id")
    accounts_resp = await plaid.get_accounts(access_token)
    accounts = accounts_resp.get("accounts", [])

    # 2. Encrypt the access token, bound to the owning user (AAD).
    token_enc = encrypt(access_token, aad=user_id)

    # 3. Persist within tenant context (RLS). Idempotent on relink via plaid_item_id.
    async with db.with_tenant(tenant_id) as conn:
        item_id = await conn.fetchval(
            """INSERT INTO plaid_items
                   (user_id, tenant_id, plaid_item_id, access_token_enc, item_status, institution_id)
               VALUES ($1, $2, $3, $4, 'good', $5)
               ON CONFLICT (plaid_item_id) DO UPDATE
                   SET access_token_enc = EXCLUDED.access_token_enc,
                       item_status = 'good',
                       institution_id = EXCLUDED.institution_id
               RETURNING item_id""",
            user_id,
            tenant_id,
            plaid_item_id,
            token_enc,
            institution_id,
        )
        for acc in accounts:
            bal = acc.get("balances") or {}
            await conn.execute(
                """INSERT INTO plaid_accounts
                       (item_id, tenant_id, plaid_account_id, name, official_name, type, subtype,
                        balance_current, balance_available, balance_limit, currency_code, synced_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11, NOW())
                   ON CONFLICT (plaid_account_id) DO UPDATE
                       SET balance_current = EXCLUDED.balance_current,
                           balance_available = EXCLUDED.balance_available,
                           balance_limit = EXCLUDED.balance_limit,
                           synced_at = NOW()""",
                item_id,
                tenant_id,
                acc["account_id"],
                acc.get("name"),
                acc.get("official_name"),
                acc.get("type"),
                acc.get("subtype"),
                to_money(bal.get("current")),
                to_money(bal.get("available")),
                to_money(bal.get("limit")),
                bal.get("iso_currency_code") or "USD",
            )

    await audit(
        "plaid.item_linked", user_id=user_id, tenant_id=tenant_id,
        resource="plaid_item", resource_id=str(item_id), ip_address=ip,
        metadata={"institution_id": institution_id, "accounts": len(accounts)},
    )

    # 4. Kick off syncs in the background.
    _spawn_sync(str(item_id), tenant_id, user_id)

    return {"item_id": str(item_id), "institution_name": None, "accounts_linked": len(accounts)}


async def list_items(user_id: str, tenant_id: str) -> list[dict[str, Any]]:
    async with db.with_tenant(tenant_id) as conn:
        items = await conn.fetch(
            """SELECT item_id, institution_name, item_status, last_sync_at
                 FROM plaid_items WHERE user_id = $1 ORDER BY created_at DESC""",
            user_id,
        )
        result: list[dict[str, Any]] = []
        for it in items:
            accs = await conn.fetch(
                """SELECT account_id, name, type, subtype, balance_current, currency_code
                     FROM plaid_accounts WHERE item_id = $1 ORDER BY created_at""",
                it["item_id"],
            )
            result.append(
                {
                    "item_id": str(it["item_id"]),
                    "institution_name": it["institution_name"],
                    "item_status": it["item_status"],
                    "last_sync_at": it["last_sync_at"],
                    "accounts": [
                        {
                            "account_id": str(a["account_id"]),
                            "name": a["name"],
                            "type": a["type"],
                            "subtype": a["subtype"],
                            "balance_current": a["balance_current"],
                            "currency_code": a["currency_code"],
                        }
                        for a in accs
                    ],
                }
            )
    return result


async def disconnect_item(user_id: str, tenant_id: str, item_id: str, ip: str | None) -> None:
    async with db.with_tenant(tenant_id) as conn:
        row = await conn.fetchrow(
            "SELECT access_token_enc FROM plaid_items WHERE item_id = $1 AND user_id = $2",
            item_id,
            user_id,
        )
        if not row:
            raise ApiError("NOT_FOUND")

    # Best-effort revoke at Plaid, then delete locally (cascade) regardless.
    try:
        access_token = decrypt(bytes(row["access_token_enc"]), aad=user_id)
        await get_plaid().item_remove(access_token)
    except ApiError as err:
        logger.warning("plaid item_remove failed; deleting locally anyway", error_message=str(err))

    async with db.with_tenant(tenant_id) as conn:
        await conn.execute("DELETE FROM plaid_items WHERE item_id = $1 AND user_id = $2", item_id, user_id)

    await audit("plaid.item_disconnected", user_id=user_id, tenant_id=tenant_id,
                resource="plaid_item", resource_id=item_id, ip_address=ip)


# Bounds in-process background syncs so a burst of webhooks / relinks can't
# spawn unbounded tasks and exhaust the DB pool or memory. Cross-instance
# de-duplication is handled by the Redis per-item lock in sync.py.
# (Production replaces this whole mechanism with SQS + a worker fleet.)
_MAX_CONCURRENT_SYNCS = 5
_sync_semaphore = asyncio.Semaphore(_MAX_CONCURRENT_SYNCS)
_background_tasks: set[asyncio.Task[Any]] = set()


async def _guarded_sync(item_id: str, tenant_id: str, user_id: str) -> None:
    async with _sync_semaphore:
        await run_sync_for_item(item_id, tenant_id, user_id)
    async with _sync_semaphore:
        await sync_liabilities_for_item(item_id, tenant_id, user_id)
    async with _sync_semaphore:
        await sync_investments_for_item(item_id, tenant_id, user_id)


def _spawn_sync(item_id: str, tenant_id: str, user_id: str) -> None:
    task = asyncio.create_task(_guarded_sync(item_id, tenant_id, user_id))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    def _log_failure(t: asyncio.Task[Any]) -> None:
        if t.cancelled():
            return
        exc = t.exception()
        if exc is not None:
            logger.error("background sync failed", error_message=str(exc))

    task.add_done_callback(_log_failure)
