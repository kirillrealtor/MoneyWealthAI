"""Idempotent Plaid transaction sync.

Idempotency guarantees:
  * a Redis lock per item prevents concurrent syncs across the whole fleet;
  * Plaid's `cursor` means a replay returns only deltas (re-running is safe);
  * `ON CONFLICT (plaid_transaction_id, date) DO NOTHING` makes inserts
    repeatable — a retried page never duplicates a transaction.
Network calls happen OUTSIDE the DB transaction; each page is written in a
short tenant-scoped transaction so we never hold a connection across the wire.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from app import db
from app.audit import audit
from app.encryption import decrypt
from app.integrations.plaid_client import get_plaid
from app.logging_conf import logger
from app.redis_client import redis_client

_LOCK_TTL_S = 600


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def to_money(value: Any) -> Decimal | None:
    """Convert a Plaid JSON number to Decimal without float rounding error."""
    if value is None:
        return None
    return Decimal(str(value))


async def run_sync_for_item(item_id: str, tenant_id: str, user_id: str) -> int:
    """Sync one item, managing a self-owned sync_jobs record. Used by direct
    callers (and tests). The durable worker path uses sync_item_core() instead,
    because it owns the job lifecycle itself (claim -> run -> terminal/retry).
    Returns the count of new transactions added; safe to call repeatedly."""
    sync_id: str | None = None
    try:
        async with db.with_tenant(tenant_id) as conn:
            sync_id = await conn.fetchval(
                """INSERT INTO sync_jobs (user_id, tenant_id, item_id, status)
                   VALUES ($1, $2, $3, 'running') RETURNING sync_id""",
                user_id, tenant_id, item_id,
            )
        total_added = await sync_item_core(item_id, tenant_id, user_id)
        async with db.with_tenant(tenant_id) as conn:
            await conn.execute(
                "UPDATE sync_jobs SET status = 'completed', transactions_synced = $1, "
                "completed_at = NOW() WHERE sync_id = $2",
                total_added, sync_id,
            )
        return total_added
    except Exception as err:  # noqa: BLE001
        if sync_id is not None:
            try:
                async with db.with_tenant(tenant_id) as conn:
                    await conn.execute(
                        "UPDATE sync_jobs SET status = 'failed', error_message = $1 WHERE sync_id = $2",
                        str(err)[:500], sync_id,
                    )
            except Exception:  # noqa: BLE001
                pass
        raise


async def sync_item_core(item_id: str, tenant_id: str, user_id: str) -> int:
    """Do the actual Plaid sync for one item WITHOUT touching sync_jobs (the
    caller owns the job record). Returns count of new transactions added. A
    fleet-wide Redis lock makes it safe to call concurrently — a second caller
    for the same item is skipped rather than racing."""
    lock_key = f"plaidsync:{item_id}"
    got_lock = await redis_client.set(lock_key, "1", nx=True, ex=_LOCK_TTL_S)
    if not got_lock:
        logger.info("sync already running; skipping", service="plaid-sync", item_id=item_id)
        return 0

    try:
        async with db.with_tenant(tenant_id) as conn:
            item = await conn.fetchrow(
                "SELECT access_token_enc, cursor FROM plaid_items WHERE item_id = $1", item_id
            )
            if not item:
                return 0
            accounts = await conn.fetch(
                "SELECT account_id, plaid_account_id FROM plaid_accounts WHERE item_id = $1", item_id
            )

        acct_map = {a["plaid_account_id"]: a["account_id"] for a in accounts}
        token = decrypt(bytes(item["access_token_enc"]), aad=user_id)
        cursor = item["cursor"]
        plaid = get_plaid()

        total_added = 0
        has_more = True
        while has_more:
            resp = await plaid.transactions_sync(token, cursor)
            added = resp.get("added", [])
            modified = resp.get("modified", [])
            removed = resp.get("removed", [])
            next_cursor = resp.get("next_cursor")
            has_more = bool(resp.get("has_more"))

            # Build batched rows. Money is parsed via Decimal(str(...)) so we
            # never let binary float error into a NUMERIC money column.
            upserts: list[tuple[Any, ...]] = []
            for tx in added + modified:
                account_id = acct_map.get(tx.get("account_id"))
                if account_id is None:
                    continue  # transaction for an account we don't track yet
                pfc = tx.get("personal_finance_category") or {}
                upserts.append((
                    account_id, tenant_id, tx["transaction_id"], to_money(tx.get("amount")),
                    tx.get("iso_currency_code") or "USD",
                    _parse_date(tx.get("date")), _parse_date(tx.get("authorized_date")),
                    tx.get("merchant_name") or tx.get("name"),
                    pfc.get("detailed"), pfc.get("primary"), bool(tx.get("pending")),
                ))
            removed_ids = [(tx.get("transaction_id"),) for tx in removed if tx.get("transaction_id")]

            async with db.with_tenant(tenant_id) as conn:
                if upserts:
                    await conn.executemany(
                        """INSERT INTO transactions
                               (account_id, tenant_id, plaid_transaction_id, amount, iso_currency_code,
                                date, authorized_date, merchant_name, plaid_category, category, pending)
                           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                           ON CONFLICT (plaid_transaction_id, date) DO UPDATE
                               SET amount = EXCLUDED.amount,
                                   merchant_name = EXCLUDED.merchant_name,
                                   category = EXCLUDED.category,
                                   pending = EXCLUDED.pending""",
                        upserts,
                    )
                if removed_ids:
                    await conn.executemany(
                        "DELETE FROM transactions WHERE plaid_transaction_id = $1", removed_ids
                    )
                await conn.execute(
                    "UPDATE plaid_items SET cursor = $1, last_sync_at = NOW() WHERE item_id = $2",
                    next_cursor, item_id,
                )

            cursor = next_cursor
            total_added += len(added)

        await audit("plaid.sync_completed", user_id=user_id, tenant_id=tenant_id,
                    resource="plaid_item", resource_id=item_id, metadata={"added": total_added})
        logger.info("sync completed", service="plaid-sync", item_id=item_id, added=total_added)
        return total_added

    except Exception as err:  # noqa: BLE001 - logged; job status owned by caller
        logger.error("sync failed", service="plaid-sync", item_id=item_id, error_message=str(err))
        raise
    finally:
        await redis_client.delete(lock_key)
