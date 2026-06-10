"""Notification dispatcher — the single send path.

Guarantees:
  * Idempotent: a Redis dedupe key (24h) + a UNIQUE(dedupe_key, channel) outbox
    constraint mean retries and overlapping replicas never double-notify a user
    (spamming users is itself a trust/compliance failure).
  * Preference-aware: respects per-type toggles, channel opt-ins, TCPA SMS
    opt-in, and quiet hours.
  * Tenant-scoped: every write runs inside with_tenant() (FORCE-RLS tables).
"""
from __future__ import annotations

from dataclasses import dataclass

import asyncpg

from app import db
from app.logging_conf import logger
from app.redis_client import redis_client

from . import channels
from .preferences import in_quiet_hours

_DEDUP_TTL_S = 86400

# Which preference toggle gates each alert type.
_TYPE_PREF = {
    "budget_threshold": "budget_alerts", "budget_overpace": "budget_alerts",
    "goal_behind": "goal_alerts", "goal_milestone": "goal_alerts",
    "unusual_transaction": "unusual_tx_alerts",
    "bank_connection_error": "bank_error_alerts", "bank_token_expiring": "bank_error_alerts",
}
# Candidate non-in-app channels per type (in-app is always recorded as an alert row).
_TYPE_CHANNELS = {
    "budget_threshold": ["push"], "budget_overpace": ["push"],
    "goal_behind": ["email"], "goal_milestone": ["push", "email"],
    "unusual_transaction": ["push", "email"],
    "bank_connection_error": ["push", "email"], "bank_token_expiring": ["email"],
}


@dataclass
class AlertSpec:
    type: str
    title: str
    body: str
    severity: str       # info | warning | critical
    dedupe_key: str     # stable per (user, logical event)


def _resolve_channels(alert_type: str, prefs: dict[str, object]) -> list[str]:
    quiet = in_quiet_hours(prefs)
    out: list[str] = []
    for ch in _TYPE_CHANNELS.get(alert_type, []):
        if not channels.is_configured(ch):
            continue
        if ch == "email" and prefs.get("email_enabled", True):
            out.append(ch)
        elif ch == "push" and prefs.get("push_enabled", True) and not quiet:
            out.append(ch)
        elif ch == "sms" and prefs.get("sms_opt_in", False) and not quiet:
            out.append(ch)
    return out


async def send_notification(user_id: str, tenant_id: str, spec: AlertSpec, prefs: dict[str, object]) -> bool:
    """Dispatch one alert. Returns True if newly delivered, False if deduped or
    suppressed by preferences."""
    # 1. Type toggle off -> the user has opted out of this category entirely.
    toggle = _TYPE_PREF.get(spec.type)
    if toggle and not prefs.get(toggle, True):
        return False

    # 2. Idempotency gate (fail-open on Redis; the outbox UNIQUE is the backstop).
    rkey = f"notif:{user_id}:{spec.dedupe_key}"
    try:
        if not await redis_client.set(rkey, "1", nx=True, ex=_DEDUP_TTL_S):
            return False
    except Exception as err:  # noqa: BLE001
        logger.warning("notif dedup redis failed open", service="notifications", error_message=str(err))

    chans = _resolve_channels(spec.type, prefs)

    # 3. In-app notification = an alerts row (always recorded).
    async with db.with_tenant(tenant_id) as conn:
        alert_id = await conn.fetchval(
            """INSERT INTO alerts (user_id, tenant_id, type, title, body, severity, sent_via)
               VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING alert_id""",
            user_id, tenant_id, spec.type, spec.title, spec.body, spec.severity,
            ["in_app", *chans],
        )

    # 4. Other channels via the outbox (idempotent on (dedupe_key, channel)).
    to_email = None
    if "email" in chans:
        async with db.with_tenant(tenant_id) as conn:
            to_email = await conn.fetchval("SELECT email FROM users WHERE user_id = $1", user_id)
    for ch in chans:
        await _deliver_via_outbox(user_id, tenant_id, str(alert_id), ch, spec, to_email)
    return True


async def _deliver_via_outbox(
    user_id: str, tenant_id: str, alert_id: str, channel: str, spec: AlertSpec, to_email: str | None
) -> None:
    async with db.with_tenant(tenant_id) as conn:
        try:
            outbox_id = await conn.fetchval(
                """INSERT INTO notification_outbox (user_id, tenant_id, alert_id, channel, dedupe_key)
                   VALUES ($1,$2,$3,$4,$5) RETURNING outbox_id""",
                user_id, tenant_id, alert_id, channel, spec.dedupe_key,
            )
        except asyncpg.UniqueViolationError:
            return  # already queued for this channel — at-least-once, never twice

    ok = await channels.deliver(channel, to_email=to_email, title=spec.title, body=spec.body)
    async with db.with_tenant(tenant_id) as conn:
        await conn.execute(
            """UPDATE notification_outbox
                  SET status = $1, attempts = attempts + 1,
                      sent_at = CASE WHEN $1 = 'sent' THEN NOW() ELSE sent_at END,
                      error = $2
                WHERE outbox_id = $3""",
            "sent" if ok else "failed", None if ok else "delivery_failed", outbox_id,
        )
