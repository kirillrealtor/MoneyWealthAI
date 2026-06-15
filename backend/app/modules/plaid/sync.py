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
from app.config import settings
from app.encryption import decrypt
from app.errors import ApiError
from app.integrations.plaid_client import get_plaid
from app.logging_conf import logger
from app.redis_client import redis_client

_LOCK_TTL_S = 600

# Plaid security `type` -> the portfolio dashboard's allocation buckets.
_ASSET_CLASS = {
    "equity": "equity",
    "etf": "equity",
    "mutual fund": "equity",
    "fixed income": "fixed_income",
    "cash": "cash",
    "money market": "cash",
}


def _pct_to_fraction(pct: Any) -> Decimal | None:
    """Plaid returns APR/interest as a PERCENTAGE (e.g. 24.99). debt_accounts.apr
    is NUMERIC(6,4) and the calc engine expects a FRACTION (0.2499) — divide by
    100, or every interest/payoff figure would be 100x wrong."""
    if pct is None:
        return None
    return (Decimal(str(pct)) / Decimal(100)).quantize(Decimal("0.0001"))


def _num(value: Any, places: str = "0.000001") -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal(places))


def _asset_class(plaid_type: Any) -> str:
    return _ASSET_CLASS.get(str(plaid_type or "").lower(), "alternative")


def _pick_apr(aprs: Any) -> Decimal | None:
    """Choose the most representative APR from a credit card's apr list."""
    items = aprs or []
    if not items:
        return None
    purchase = next((a for a in items if a.get("apr_type") == "purchase_apr"), None)
    chosen = purchase or items[0]
    return _pct_to_fraction(chosen.get("apr_percentage"))


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

        # Liabilities (-> debt) and investments (-> portfolio). Each is best-effort:
        # an item without that product, or a transient Plaid error, must not fail
        # the transaction sync that already succeeded.
        if "liabilities" in settings.plaid_products_list:
            await _sync_liabilities(token, acct_map, tenant_id)
        if "investments" in settings.plaid_products_list:
            await _sync_investments(token, acct_map, tenant_id)

        await audit("plaid.sync_completed", user_id=user_id, tenant_id=tenant_id,
                    resource="plaid_item", resource_id=item_id, metadata={"added": total_added})
        logger.info("sync completed", service="plaid-sync", item_id=item_id, added=total_added)
        return total_added

    except Exception as err:  # noqa: BLE001 - logged; job status owned by caller
        logger.error("sync failed", service="plaid-sync", item_id=item_id, error_message=str(err))
        raise
    finally:
        await redis_client.delete(lock_key)


async def _sync_liabilities(token: str, acct_map: dict[str, Any], tenant_id: str) -> None:
    """Snapshot credit cards / student loans / mortgages into debt_accounts."""
    try:
        resp = await get_plaid().liabilities_get(token)
    except ApiError as err:
        logger.info("liabilities unavailable; skipping", service="plaid-sync", error_message=str(err))
        return

    balances = {a["account_id"]: (a.get("balances") or {}).get("current") for a in resp.get("accounts", [])}
    liab = resp.get("liabilities") or {}
    rows: list[tuple[Any, ...]] = []

    def add(plaid_aid: Any, apr: Decimal | None, minimum: Any, last_pay: Any, kind: str) -> None:
        aid = acct_map.get(plaid_aid)
        if aid is None:
            return
        rows.append((aid, tenant_id, to_money(balances.get(plaid_aid)), apr,
                     to_money(minimum), _parse_date(last_pay), kind))

    for c in liab.get("credit") or []:
        add(c.get("account_id"), _pick_apr(c.get("aprs")), c.get("minimum_payment_amount"),
            c.get("last_payment_date"), "credit")
    for s in liab.get("student") or []:
        add(s.get("account_id"), _pct_to_fraction(s.get("interest_rate_percentage")),
            s.get("minimum_payment_amount"), s.get("last_payment_date"), "student")
    for m in liab.get("mortgage") or []:
        add(m.get("account_id"), _pct_to_fraction((m.get("interest_rate") or {}).get("percentage")),
            m.get("next_monthly_payment"), m.get("last_payment_date"), "mortgage")

    if not rows:
        return
    account_ids = list({r[0] for r in rows})
    async with db.with_tenant(tenant_id) as conn:
        await conn.execute("DELETE FROM debt_accounts WHERE account_id = ANY($1::uuid[])", account_ids)
        await conn.executemany(
            """INSERT INTO debt_accounts
                   (account_id, tenant_id, balance, apr, minimum_payment, last_payment_at, debt_type, synced_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())""",
            rows,
        )
    logger.info("liabilities synced", service="plaid-sync", debts=len(rows))


async def _sync_investments(token: str, acct_map: dict[str, Any], tenant_id: str) -> None:
    """Snapshot investment holdings into portfolio_holdings."""
    try:
        resp = await get_plaid().investments_holdings_get(token)
    except ApiError as err:
        logger.info("investments unavailable; skipping", service="plaid-sync", error_message=str(err))
        return

    securities = {s["security_id"]: s for s in resp.get("securities", [])}
    rows: list[tuple[Any, ...]] = []
    for h in resp.get("holdings", []):
        aid = acct_map.get(h.get("account_id"))
        if aid is None:
            continue
        sec = securities.get(h.get("security_id"), {})
        rows.append((
            aid, tenant_id, h.get("security_id"), sec.get("ticker_symbol"), sec.get("name"),
            _num(h.get("quantity")), to_money(h.get("cost_basis")),
            _num(h.get("institution_price"), "0.0001"), to_money(h.get("institution_value")),
            _asset_class(sec.get("type")), sec.get("sector"),
        ))

    if not rows:
        return
    account_ids = list({r[0] for r in rows})
    async with db.with_tenant(tenant_id) as conn:
        await conn.execute("DELETE FROM portfolio_holdings WHERE account_id = ANY($1::uuid[])", account_ids)
        await conn.executemany(
            """INSERT INTO portfolio_holdings
                   (account_id, tenant_id, plaid_security_id, ticker, name, quantity, cost_basis,
                    institution_price, institution_value, asset_class, sector, synced_at)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11, NOW())""",
            rows,
        )
    logger.info("investments synced", service="plaid-sync", holdings=len(rows))
