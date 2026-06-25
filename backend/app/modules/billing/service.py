"""Billing logic (Stripe). Stripe is the source of truth for subscription state;
the signature-verified webhook syncs it into `subscriptions` + `users.tier`.

Stripe's SDK is synchronous, so each call runs in a threadpool to avoid blocking
the event loop.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, cast

import stripe
from starlette.concurrency import run_in_threadpool

from app import db
from app.audit import audit
from app.config import settings
from app.errors import ApiError
from app.logging_conf import logger

_ACTIVE = {"active", "trialing"}


def _stripe() -> Any:
    if not settings.stripe_configured:
        raise ApiError("BILLING_UNAVAILABLE")
    stripe.api_key = settings.stripe_secret_key
    return stripe


async def _ensure_customer(user_id: str, tenant_id: str, email: str) -> str:
    async with db.with_tenant(tenant_id, user_id) as conn:
        existing = await conn.fetchval("SELECT stripe_customer_id FROM users WHERE user_id = $1", user_id)
    if existing:
        return cast(str, existing)

    s = _stripe()
    customer = await run_in_threadpool(
        lambda: s.Customer.create(email=email, metadata={"user_id": user_id, "tenant_id": tenant_id})
    )
    async with db.with_tenant(tenant_id, user_id) as conn:
        await conn.execute("UPDATE users SET stripe_customer_id = $1 WHERE user_id = $2", customer.id, user_id)
    return cast(str, customer.id)


async def create_checkout(user_id: str, tenant_id: str, email: str, plan: str, interval: str) -> str:
    s = _stripe()  # raises BILLING_UNAVAILABLE if Stripe isn't configured
    price = settings.stripe_price_id(plan, interval)
    if not price:
        raise ApiError("VALIDATION_ERROR", message="That plan isn't available.")
    customer_id = await _ensure_customer(user_id, tenant_id, email)
    meta = {"user_id": user_id, "tenant_id": tenant_id, "tier": plan}
    session = await run_in_threadpool(
        lambda: s.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": price, "quantity": 1}],
            success_url=f"{settings.web_app_url}/app/settings?billing=success",
            cancel_url=f"{settings.web_app_url}/pricing?billing=cancelled",
            subscription_data={"metadata": meta},
            metadata=meta,
            allow_promotion_codes=True,
        )
    )
    return cast(str, session.url)


async def create_portal(user_id: str, tenant_id: str) -> str:
    async with db.with_tenant(tenant_id, user_id) as conn:
        customer_id = await conn.fetchval("SELECT stripe_customer_id FROM users WHERE user_id = $1", user_id)
    if not customer_id:
        raise ApiError("NOT_FOUND", message="No billing account yet.")
    s = _stripe()
    session = await run_in_threadpool(
        lambda: s.billing_portal.Session.create(
            customer=customer_id, return_url=f"{settings.web_app_url}/app/settings"
        )
    )
    return cast(str, session.url)


async def get_subscription(user_id: str, tenant_id: str) -> dict[str, Any] | None:
    async with db.with_tenant(tenant_id, user_id) as conn:
        row = await conn.fetchrow(
            """SELECT tier, status, current_period_end, cancel_at_period_end
                 FROM subscriptions
                WHERE user_id = $1 AND status = ANY($2)
                ORDER BY updated_at DESC LIMIT 1""",
            user_id,
            list(_ACTIVE | {"past_due"}),
        )
    return dict(row) if row else None


async def handle_webhook(payload: bytes, signature: str | None) -> None:
    if not settings.stripe_webhook_secret:
        raise ApiError("BILLING_UNAVAILABLE")
    _stripe()
    try:
        event = stripe.Webhook.construct_event(  # type: ignore[no-untyped-call]
            payload, signature or "", settings.stripe_webhook_secret
        )
    except Exception as err:  # noqa: BLE001 - bad signature / malformed
        logger.warning("stripe webhook verification failed", error_message=str(err))
        raise ApiError("UNAUTHORIZED", message="Invalid webhook signature.") from err

    if event["type"].startswith("customer.subscription."):
        await _sync_subscription(cast(dict[str, Any], event["data"]["object"]))


async def _sync_subscription(sub: dict[str, Any]) -> None:
    meta = sub.get("metadata") or {}
    user_id, tenant_id, tier = meta.get("user_id"), meta.get("tenant_id"), meta.get("tier")
    if not (user_id and tenant_id and tier):
        logger.warning("subscription event missing metadata; skipping", sub_id=sub.get("id"))
        return

    status = str(sub.get("status"))
    period_end = sub.get("current_period_end")
    cpe = datetime.fromtimestamp(int(period_end), timezone.utc) if period_end else None
    new_tier = tier if status in _ACTIVE else "free"

    async with db.with_tenant(tenant_id, user_id) as conn:
        await conn.execute(
            """INSERT INTO subscriptions
                   (user_id, tenant_id, stripe_subscription_id, stripe_customer_id,
                    status, tier, current_period_end, cancel_at_period_end)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
               ON CONFLICT (stripe_subscription_id) DO UPDATE
                   SET status = EXCLUDED.status, tier = EXCLUDED.tier,
                       current_period_end = EXCLUDED.current_period_end,
                       cancel_at_period_end = EXCLUDED.cancel_at_period_end, updated_at = NOW()""",
            user_id, tenant_id, sub["id"], sub.get("customer"), status, tier, cpe,
            bool(sub.get("cancel_at_period_end")),
        )
        # users.tier is the synced cache the app gates on.
        await conn.execute("UPDATE users SET tier = $1 WHERE user_id = $2", new_tier, user_id)

    await audit("billing.subscription_synced", user_id=user_id, tenant_id=tenant_id,
                resource="subscription", resource_id=str(sub["id"]),
                metadata={"status": status, "tier": new_tier})
    logger.info("subscription synced", user_id=user_id, status=status, tier=new_tier)
