"""Plaid webhook verification + dispatch.

Verification (defense against forged webhooks):
  1. The `Plaid-Verification` header is a JWT (ES256). Decode its header to get
     the key id (kid); reject any other algorithm.
  2. Fetch the matching verification key (JWK) from Plaid, cached briefly.
  3. Verify the JWT signature with that key.
  4. Enforce freshness (iat within 5 min) to blunt replay.
  5. Constant-time compare SHA-256(raw body) to the signed claim.
Only after all five do we trust and act on the payload.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from typing import Any

import jwt
from jwt.algorithms import ECAlgorithm

from app.errors import ApiError
from app.integrations.plaid_client import get_plaid
from app.logging_conf import logger
from app.redis_client import redis_client

_MAX_AGE_S = 300
_KEY_CACHE_TTL_S = 3600
_NEG_CACHE_TTL_S = 300
_NEG_SENTINEL = "__none__"
# Plaid key ids are short, safe tokens. Reject anything else BEFORE any network
# call so a flood of bogus `kid`s can't amplify into Plaid API calls (DoS/cost).
_KID_RE = re.compile(r"^[A-Za-z0-9_-]{1,100}$")


async def _get_verification_key(kid: str) -> dict[str, Any] | None:
    if not _KID_RE.match(kid):
        return None
    cache_key = f"plaid:jwk:{kid}"
    cached = await redis_client.get(cache_key)
    if cached == _NEG_SENTINEL:
        return None
    if cached:
        return json.loads(cached)  # type: ignore[no-any-return]
    try:
        resp = await get_plaid().webhook_verification_key_get(kid)
    except ApiError:
        # Unknown kid / Plaid error: negative-cache so repeats don't re-hit Plaid.
        await redis_client.set(cache_key, _NEG_SENTINEL, ex=_NEG_CACHE_TTL_S)
        return None
    key: dict[str, Any] | None = resp.get("key")
    if key:
        await redis_client.set(cache_key, json.dumps(key), ex=_KEY_CACHE_TTL_S)
    else:
        await redis_client.set(cache_key, _NEG_SENTINEL, ex=_NEG_CACHE_TTL_S)
    return key


async def verify_webhook(raw_body: bytes, verification_header: str | None) -> bool:
    if not verification_header:
        return False
    try:
        header = jwt.get_unverified_header(verification_header)
    except jwt.PyJWTError:
        return False
    if header.get("alg") != "ES256" or "kid" not in header:
        return False

    jwk = await _get_verification_key(header["kid"])
    if not jwk:
        return False

    try:
        # from_jwk returns a public key for a public JWK; jwt.decode accepts it.
        public_key = ECAlgorithm.from_jwk(json.dumps(jwk))
        claims = jwt.decode(verification_header, public_key, algorithms=["ES256"])  # type: ignore[arg-type]
    except jwt.PyJWTError as err:
        logger.warning("plaid webhook jwt invalid", service="plaid", error_message=str(err))
        return False

    iat = claims.get("iat", 0)
    if abs(time.time() - iat) > _MAX_AGE_S:
        logger.warning("plaid webhook stale (replay?)", service="plaid")
        return False

    body_hash = hashlib.sha256(raw_body).hexdigest()
    claimed = claims.get("request_body_sha256", "")
    if not hmac.compare_digest(body_hash, claimed):
        logger.warning("plaid webhook body hash mismatch", service="plaid")
        return False
    return True


async def dispatch_webhook(payload: dict[str, Any]) -> None:
    """Act on a VERIFIED webhook. Resolves the tenant via a SECURITY DEFINER
    function (the one legitimate cross-tenant lookup) then enqueues work."""
    from app import db
    from app.modules.plaid.service import _spawn_sync

    webhook_type = payload.get("webhook_type")
    webhook_code = payload.get("webhook_code")
    plaid_item_id = payload.get("item_id")
    if not plaid_item_id:
        return

    row = await db.fetchrow("SELECT * FROM resolve_plaid_item($1)", plaid_item_id)
    if not row:
        logger.warning("webhook for unknown item", service="plaid")
        return
    item_id, user_id, tenant_id = str(row["item_id"]), str(row["user_id"]), str(row["tenant_id"])

    from app.notifications.dispatch import AlertSpec, send_notification
    from app.notifications.preferences import load_preferences

    _tx_codes = {"SYNC_UPDATES_AVAILABLE", "DEFAULT_UPDATE", "INITIAL_UPDATE"}
    if webhook_type == "TRANSACTIONS" and webhook_code in _tx_codes:
        _spawn_sync(item_id, tenant_id, user_id)
    elif webhook_type == "ITEM" and webhook_code == "ERROR":
        async with db.with_tenant(tenant_id) as conn:
            await conn.execute("UPDATE plaid_items SET item_status = 'error' WHERE item_id = $1", item_id)
        prefs = await load_preferences(user_id, tenant_id)
        await send_notification(user_id, tenant_id, AlertSpec(
            "bank_connection_error", "Bank connection needs attention",
            "One of your linked accounts hit a sync error. Re-link it to keep your data up to date.",
            "critical", f"bank_err:{item_id}"), prefs)
    elif webhook_type == "ITEM" and webhook_code == "PENDING_EXPIRATION":
        async with db.with_tenant(tenant_id) as conn:
            await conn.execute("UPDATE plaid_items SET item_status = 'pending_expiration' WHERE item_id = $1", item_id)
        prefs = await load_preferences(user_id, tenant_id)
        await send_notification(user_id, tenant_id, AlertSpec(
            "bank_token_expiring", "Re-link your bank soon",
            "A bank connection will expire in ~7 days. Re-link now to avoid interruption.",
            "warning", f"bank_exp:{item_id}"), prefs)
    else:
        logger.info("unhandled plaid webhook", service="plaid", webhook_type=webhook_type, webhook_code=webhook_code)
