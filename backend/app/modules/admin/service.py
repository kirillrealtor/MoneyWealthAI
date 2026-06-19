"""Admin business logic. Reads/writes go through migration-012 SECURITY DEFINER
functions; every mutation is written to audit_logs."""
from __future__ import annotations

from typing import Any

from app import db
from app.audit import audit
from app.crypto import DUMMY_PASSWORD_HASH, verify_password
from app.errors import ApiError

from .tokens import sign_admin_token


async def login(email: str, password: str, ip: str | None) -> dict[str, str]:
    row = await db.fetchrow(
        "SELECT admin_id, password_hash, role, is_active FROM admins WHERE email = $1",
        email.lower().strip(),
    )
    # Constant-ish time + generic error (no admin-account enumeration).
    stored = row["password_hash"] if row else DUMMY_PASSWORD_HASH
    if not verify_password(password, stored) or row is None or not row["is_active"]:
        raise ApiError("UNAUTHORIZED", message="Invalid email or password.")

    admin_id = str(row["admin_id"])
    await db.execute("UPDATE admins SET last_login_at = NOW() WHERE admin_id = $1", admin_id)
    await audit("admin.login", resource="admin", resource_id=admin_id, ip_address=ip,
                metadata={"admin_id": admin_id})
    return {"access_token": sign_admin_token(admin_id, row["role"]), "role": row["role"]}


async def kpis() -> dict[str, Any]:
    row = await db.fetchrow("SELECT * FROM admin_kpis()")
    return dict(row) if row else {}


async def list_users(search: str | None, limit: int, offset: int) -> list[dict[str, Any]]:
    rows = await db.fetch("SELECT * FROM admin_list_users($1, $2, $3)", search, limit, offset)
    return [{**dict(r), "user_id": str(r["user_id"])} for r in rows]


async def get_user(user_id: str) -> dict[str, Any]:
    row = await db.fetchrow("SELECT * FROM admin_get_user($1)", user_id)
    if row is None:
        raise ApiError("NOT_FOUND")
    return {**dict(row), "user_id": str(row["user_id"])}


async def update_user(
    *, admin_id: str, user_id: str, tier: str | None, suspended: bool | None,
    is_verified: bool | None, reason: str | None, ip: str | None,
) -> dict[str, Any]:
    row = await db.fetchrow(
        "SELECT * FROM admin_update_user($1, $2, $3, $4)", user_id, tier, suspended, is_verified
    )
    if row is None:
        raise ApiError("NOT_FOUND")
    await audit("admin.user_updated", user_id=user_id, resource="user", resource_id=user_id, ip_address=ip,
                metadata={"admin_id": admin_id, "tier": tier, "suspended": suspended,
                          "is_verified": is_verified, "reason": reason})
    return {**dict(row), "user_id": str(row["user_id"])}


async def ai_ops() -> dict[str, Any]:
    from app.ai.health import get_ai_stats
    from app.config import settings

    stats = await get_ai_stats()
    usage = await db.fetch("SELECT * FROM admin_ai_usage($1)", 14)
    top = await db.fetch("SELECT * FROM admin_top_token_users($1)", 10)
    return {
        "stats": stats,
        "usage": [dict(r) for r in usage],
        "top_users": [{**dict(r), "user_id": str(r["user_id"])} for r in top],
        "tier_budgets": {
            "free": settings.token_budget_free,
            "plus": settings.token_budget_plus,
            "premium": settings.token_budget_premium,
        },
    }


async def plaid_ops() -> dict[str, Any]:
    health = await db.fetchrow("SELECT * FROM admin_plaid_health()")
    jobs = await db.fetch("SELECT * FROM admin_sync_jobs($1)", 25)
    return {
        "health": dict(health) if health else {},
        "jobs": [
            {**dict(j), "sync_id": str(j["sync_id"]), "item_id": str(j["item_id"])} for j in jobs
        ],
    }


async def resync_item(*, admin_id: str, item_id: str, ip: str | None) -> None:
    from app.modules.plaid import worker

    row = await db.fetchrow("SELECT * FROM admin_resolve_item($1)", item_id)
    if row is None:
        raise ApiError("NOT_FOUND")
    user_id, tenant_id = str(row["user_id"]), str(row["tenant_id"])
    await worker.enqueue_sync(item_id, tenant_id, user_id)
    await audit("admin.plaid_resync", user_id=user_id, tenant_id=tenant_id,
                resource="plaid_item", resource_id=item_id, ip_address=ip,
                metadata={"admin_id": admin_id})


async def outbox(status: str | None, limit: int) -> list[dict[str, Any]]:
    rows = await db.fetch("SELECT * FROM admin_outbox($1, $2)", status, limit)
    return [{**dict(r), "outbox_id": str(r["outbox_id"])} for r in rows]


async def retry_outbox(*, admin_id: str, outbox_id: str, ip: str | None) -> None:
    row = await db.fetchrow("SELECT * FROM admin_outbox_retry($1)", outbox_id)
    if row is None:
        raise ApiError("NOT_FOUND", message="No failed delivery with that id.")
    await audit("admin.outbox_retry", resource="notification_outbox", ip_address=ip,
                metadata={"admin_id": admin_id, "outbox_id": outbox_id})


async def list_flags() -> list[dict[str, Any]]:
    rows = await db.fetch("SELECT key, enabled, description, updated_at FROM feature_flags ORDER BY key")
    return [dict(r) for r in rows]


async def set_flag(*, admin_id: str, key: str, enabled: bool, ip: str | None) -> dict[str, Any]:
    row = await db.fetchrow(
        """UPDATE feature_flags SET enabled = $1, updated_at = NOW()
            WHERE key = $2 RETURNING key, enabled, description, updated_at""",
        enabled, key,
    )
    if row is None:
        raise ApiError("NOT_FOUND")
    await audit("admin.flag_set", resource="feature_flag", ip_address=ip,
                metadata={"admin_id": admin_id, "key": key, "enabled": enabled})
    return dict(row)


async def audit_feed(limit: int, offset: int) -> list[dict[str, Any]]:
    rows = await db.fetch("SELECT * FROM admin_audit($1, $2)", limit, offset)
    return [
        {
            "log_id": str(r["log_id"]),
            "user_id": str(r["user_id"]) if r["user_id"] else None,
            "action": r["action"],
            "resource": r["resource"],
            "resource_id": str(r["resource_id"]) if r["resource_id"] else None,
            "ip_address": str(r["ip_address"]) if r["ip_address"] else None,
            "ts": r["ts"],
        }
        for r in rows
    ]
