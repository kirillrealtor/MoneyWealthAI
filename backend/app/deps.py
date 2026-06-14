"""FastAPI dependencies: auth guard, tenant resolution, rate limiting."""
from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, cast

import jwt
from fastapi import Depends, Request

from app import db
from app.config import settings
from app.context import get_context
from app.crypto import stable_bucket
from app.errors import ApiError
from app.logging_conf import logger
from app.modules.auth.tokens import verify_access_token
from app.redis_client import redis_client


@dataclass
class CurrentUser:
    user_id: str
    tenant_id: str
    tier: str


def _decode_access(request: Request, token: str) -> dict[str, Any]:
    """Verify the access token once per request and memoize the claims on
    request.state. Both the rate limiter and require_auth need the decoded
    token; without this the JWT signature would be verified twice per authed
    request. Raises jwt.PyJWTError on an invalid token (callers handle it).
    """
    cached = getattr(request.state, "access_claims", None)
    if cached is not None:
        return cast("dict[str, Any]", cached)
    claims = verify_access_token(token)
    request.state.access_claims = claims
    return claims


async def require_auth(request: Request) -> CurrentUser:
    """Validate the Bearer access token (stateless) and enrich request context."""
    header = request.headers.get("authorization")
    if not header or not header.startswith("Bearer "):
        raise ApiError("UNAUTHORIZED")
    try:
        claims = _decode_access(request, header[len("Bearer "):])
    except jwt.PyJWTError as err:
        raise ApiError("UNAUTHORIZED") from err

    user = CurrentUser(user_id=claims["sub"], tenant_id=claims["tenant_id"], tier=claims.get("tier", "free"))
    ctx = get_context()
    if ctx:
        ctx.user_id = user.user_id
        ctx.tenant_id = user.tenant_id
    return user


async def resolve_tenant(request: Request) -> str:
    """Resolve the active tenant for white-label routing (Architecture 6).

    Order: X-Tenant-ID header -> default retail tenant. Subdomain resolution is
    added when custom domains ship (Phase 7). RLS enforcement happens at query
    time via db.with_tenant().
    """
    header_tenant = request.headers.get("x-tenant-id")
    tenant_id = settings.default_tenant_id
    if header_tenant:
        exists = await db.fetchval(
            "SELECT tenant_id FROM tenants WHERE tenant_id = $1 AND is_active = true", header_tenant
        )
        if not exists:
            raise ApiError("FORBIDDEN", details={"reason": "Unknown or inactive tenant."})
        tenant_id = header_tenant

    ctx = get_context()
    if ctx:
        ctx.tenant_id = tenant_id
    return tenant_id


async def require_verified(user: CurrentUser = Depends(require_auth)) -> CurrentUser:
    """Gate sensitive routes behind a verified email. Login itself stays open
    (so users can re-trigger verification), but any route that touches money or
    bank data should depend on this. Building block for Phase 2+ routes:
    `Depends(require_verified)`.
    """
    async with db.with_tenant(user.tenant_id, user.user_id) as conn:
        verified = await conn.fetchval("SELECT is_verified FROM users WHERE user_id = $1", user.user_id)
    if not verified:
        raise ApiError("FORBIDDEN", details={"reason": "Email verification required."})
    return user


def rate_limit(bucket: str, limit_per_min: int) -> Callable[[Request], Awaitable[None]]:
    """Fixed-window limiter backed by Redis (Architecture 5). Keyed by user id
    when authenticated, else client IP. Fails OPEN on Redis errors so a cache
    outage cannot take down the whole API.
    """

    async def _dep(request: Request) -> None:
        # Key by stable user id when authenticated (the JWT string rotates every
        # ~15 min, which would otherwise reset the user's limit on each refresh);
        # fall back to client IP for unauthenticated routes.
        auth = request.headers.get("authorization")
        if auth and auth.startswith("Bearer "):
            try:
                identifier = "u:" + str(_decode_access(request, auth[len("Bearer "):])["sub"])
            except Exception:  # noqa: BLE001 - invalid token; key by the token itself
                identifier = "t:" + auth
        else:
            identifier = "ip:" + (request.client.host if request.client else "anon")
        window = int(time.time() // 60)
        # stable_bucket (SHA-256) instead of builtin hash() so the key is the
        # same across all instances/processes — required for a shared limit.
        key = f"rl:{bucket}:{stable_bucket(identifier)}:{window}"
        try:
            count = await redis_client.incr(key)
            if count == 1:
                await redis_client.expire(key, 60)
            if count > limit_per_min:
                raise ApiError("RATE_LIMITED")
        except ApiError:
            raise
        except Exception as err:  # noqa: BLE001 - fail open
            logger.warning("rate limiter failing open", error_type="RATE_LIMIT_DEGRADED", error_message=str(err))

    return _dep
