"""Notification preferences + quiet-hours logic (tenant-scoped)."""
from __future__ import annotations

from datetime import datetime, time
from typing import Any
from zoneinfo import ZoneInfo

from app import db
from app.logging_conf import logger

_EDITABLE = {
    "push_enabled", "email_enabled", "sms_opt_in",
    "budget_alerts", "goal_alerts", "bank_error_alerts", "unusual_tx_alerts",
    "weekly_digest", "monthly_report", "marketing_emails",
    "quiet_hours_start", "quiet_hours_end", "timezone",
}


async def load_preferences(user_id: str, tenant_id: str) -> dict[str, Any]:
    async with db.with_tenant(tenant_id) as conn:
        row = await conn.fetchrow("SELECT * FROM notification_preferences WHERE user_id = $1", user_id)
        if row is None:  # robustness — normally created at signup
            await conn.execute(
                "INSERT INTO notification_preferences (user_id, tenant_id) VALUES ($1, $2)", user_id, tenant_id
            )
            row = await conn.fetchrow("SELECT * FROM notification_preferences WHERE user_id = $1", user_id)
    return dict(row) if row else {}


async def update_preferences(user_id: str, tenant_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    cols = {k: v for k, v in fields.items() if k in _EDITABLE and v is not None}
    if cols:
        sets = ", ".join(f"{c} = ${i + 3}" for i, c in enumerate(cols))
        async with db.with_tenant(tenant_id) as conn:
            await conn.execute(
                f"UPDATE notification_preferences SET {sets}, updated_at = NOW() WHERE user_id = $1 AND tenant_id = $2",
                user_id, tenant_id, *cols.values(),
            )
    return await load_preferences(user_id, tenant_id)


def _in_window(now_t: time, start: time, end: time) -> bool:
    if start == end:
        return False
    if start < end:
        return start <= now_t < end
    return now_t >= start or now_t < end  # wraps midnight (e.g. 22:00–08:00)


def in_quiet_hours(prefs: dict[str, Any]) -> bool:
    """True if push/SMS should be suppressed right now for this user. Fails SAFE
    (returns False) on any tz problem — better to risk a notification than to
    silently swallow all of them behind a bad timezone."""
    start, end = prefs.get("quiet_hours_start"), prefs.get("quiet_hours_end")
    if not isinstance(start, time) or not isinstance(end, time):
        return False
    try:
        tz = ZoneInfo(prefs.get("timezone") or "UTC")
        now_t = datetime.now(tz).timetz().replace(tzinfo=None)
    except Exception as err:  # noqa: BLE001 - tzdata missing / bad timezone string
        logger.warning("quiet-hours tz lookup failed; not suppressing", service="notifications",
                       error_message=str(err))
        return False
    return _in_window(now_t, start, end)
