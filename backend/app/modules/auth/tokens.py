"""JWT access tokens (stateless) + opaque rotating refresh tokens (stateful)."""
from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import jwt

from app import db
from app.config import settings
from app.crypto import random_token, sha256


def sign_access_token(user_id: str, tenant_id: str, tier: str) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "tier": tier,
        "iat": now,
        "exp": now + settings.access_token_ttl,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    return jwt.encode(payload, settings.jwt_access_secret, algorithm="HS256")


def verify_access_token(token: str) -> dict[str, Any]:
    # Verifies signature AND issuer/audience — a token minted for a different
    # service/audience is rejected even if signed with a leaked key elsewhere.
    return cast(
        "dict[str, Any]",
        jwt.decode(
            token,
            settings.jwt_access_secret,
            algorithms=["HS256"],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        ),
    )


async def issue_refresh_token(
    user_id: str, tenant_id: str, ip: str | None, user_agent: str | None
) -> str:
    """Issue an opaque refresh token; persist only its SHA-256 (Architecture 6).

    tenant_id is stored so the refresh path can resolve the tenant without a
    circular read of the RLS-protected users table.
    """
    raw = random_token(48)
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.refresh_token_ttl)
    await db.execute(
        """INSERT INTO user_sessions (user_id, tenant_id, token_hash, ip_address, user_agent, expires_at)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        user_id,
        tenant_id,
        sha256(raw),
        ip,
        user_agent,
        expires_at,
    )
    return raw


async def find_live_session(raw_token: str) -> dict[str, Any] | None:
    row = await db.fetchrow(
        """SELECT session_id, user_id, tenant_id, expires_at, revoked_at
             FROM user_sessions
            WHERE token_hash = $1 AND revoked_at IS NULL AND expires_at > NOW()""",
        sha256(raw_token),
    )
    return dict(row) if row else None


async def rotate_refresh_token(
    session_id: str, user_id: str, tenant_id: str, ip: str | None, user_agent: str | None
) -> str:
    """Revoke the presented session and issue a new one. Reuse of the old
    (now-revoked) token is then rejected by find_live_session."""
    await db.execute("UPDATE user_sessions SET revoked_at = NOW() WHERE session_id = $1", session_id)
    return await issue_refresh_token(user_id, tenant_id, ip, user_agent)


async def find_session_including_revoked(raw_token: str) -> dict[str, Any] | None:
    """Look up a session by token regardless of revoked/expired state. Used to
    detect refresh-token REUSE (a revoked token being presented again)."""
    row = await db.fetchrow(
        "SELECT session_id, user_id, tenant_id, revoked_at FROM user_sessions WHERE token_hash = $1",
        sha256(raw_token),
    )
    return dict(row) if row else None


async def revoke_session(raw_token: str) -> None:
    await db.execute("UPDATE user_sessions SET revoked_at = NOW() WHERE token_hash = $1", sha256(raw_token))


async def revoke_all_sessions(user_id: str) -> None:
    await db.execute(
        "UPDATE user_sessions SET revoked_at = NOW() WHERE user_id = $1 AND revoked_at IS NULL", user_id
    )
