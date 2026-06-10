"""Notifications service — in-app feed (alerts) + read state. Tenant-scoped."""
from __future__ import annotations

from typing import Any

from app import db
from app.errors import ApiError


async def list_notifications(user_id: str, tenant_id: str, limit: int = 50) -> dict[str, Any]:
    async with db.with_tenant(tenant_id) as conn:
        rows = await conn.fetch(
            """SELECT alert_id, type, title, body, severity, is_read, created_at
                 FROM alerts WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2""",
            user_id, limit,
        )
        unread = await conn.fetchval(
            "SELECT COUNT(*) FROM alerts WHERE user_id = $1 AND is_read = false", user_id
        )
    items = [{"alert_id": str(r["alert_id"]), "type": r["type"], "title": r["title"], "body": r["body"],
              "severity": r["severity"], "is_read": r["is_read"], "created_at": r["created_at"]} for r in rows]
    return {"items": items, "unread_count": int(unread or 0)}


async def mark_read(user_id: str, tenant_id: str, alert_id: str) -> None:
    async with db.with_tenant(tenant_id) as conn:
        result = await conn.execute(
            "UPDATE alerts SET is_read = true WHERE alert_id = $1 AND user_id = $2", alert_id, user_id
        )
    if result.split()[-1] == "0":
        raise ApiError("NOT_FOUND")


async def mark_all_read(user_id: str, tenant_id: str) -> None:
    async with db.with_tenant(tenant_id) as conn:
        await conn.execute(
            "UPDATE alerts SET is_read = true WHERE user_id = $1 AND is_read = false", user_id
        )
