"""Cloudflare Turnstile verification.

Gated by settings.turnstile_enabled so local dev and tests run without a key
(the verifier returns True when disabled). In staging/production, set
TURNSTILE_ENABLED=true and TURNSTILE_SECRET_KEY (from Secrets Manager).

The frontend renders the Turnstile widget (site key) and submits the resulting
token; the backend validates it against Cloudflare's siteverify endpoint.
"""
from __future__ import annotations

import httpx

from app.config import settings
from app.logging_conf import logger

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
_TIMEOUT = httpx.Timeout(5.0)


async def verify_turnstile(token: str | None, remote_ip: str | None = None) -> bool:
    """Return True if the captcha token is valid (or captcha is disabled)."""
    if not settings.turnstile_enabled:
        return True
    if not settings.turnstile_secret_key:
        # Misconfiguration: enabled but no secret. Fail closed and shout.
        logger.error("turnstile enabled but no secret key set", service="captcha")
        return False
    if not token:
        return False

    data = {"secret": settings.turnstile_secret_key, "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(SITEVERIFY_URL, data=data)
        body = resp.json()
        success = bool(body.get("success"))
        if not success:
            logger.warning("turnstile verification failed", service="captcha", errors=body.get("error-codes"))
        return success
    except Exception as err:  # noqa: BLE001
        # Network/Cloudflare error: fail closed (don't let bots through on outage).
        logger.error("turnstile verify error", service="captcha", error_message=str(err))
        return False
