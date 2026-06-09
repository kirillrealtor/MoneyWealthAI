"""Append-only audit trail (schema: audit_logs).

Required for SOC 2 / GLBA and the 7-year retention requirement. Never raises
into the request path - an audit write failure is logged but does not fail the
user's action.
"""
from __future__ import annotations

import json
from typing import Any

from app import db
from app.context import get_context
from app.logging_conf import logger


async def audit(
    action: str,
    *,
    user_id: str | None = None,
    tenant_id: str | None = None,
    resource: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    ctx = get_context()
    try:
        await db.execute(
            """INSERT INTO audit_logs (user_id, tenant_id, action, resource, resource_id, ip_address, metadata)
               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            user_id or (ctx.user_id if ctx else None),
            tenant_id or (ctx.tenant_id if ctx else None),
            action,
            resource,
            resource_id,
            ip_address,
            json.dumps(metadata) if metadata is not None else None,
        )
    except Exception as err:  # noqa: BLE001 - audit must never break the request
        logger.error("audit write failed", error_type="AUDIT_WRITE_FAILED", action=action, error_message=str(err))
