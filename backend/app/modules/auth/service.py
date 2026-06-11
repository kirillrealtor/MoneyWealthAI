"""Auth business logic: signup, email verification, login, refresh, logout.

Tenant isolation: every users-table access runs inside db.with_tenant() so
Postgres Row-Level Security is enforced (the app connects as the non-owner
app_user role). Secret-token lookups (sessions, verification tokens) carry
tenant_id so the tenant can be resolved without a circular read of users.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app import db
from app.audit import audit
from app.captcha import verify_turnstile
from app.config import settings
from app.crypto import DUMMY_PASSWORD_HASH, hash_password, random_token, sha256, verify_password
from app.errors import ApiError
from app.logging_conf import logger
from app.redis_client import redis_client

from .mailer import build_verification_email, send_mail
from .tokens import (
    find_live_session,
    find_session_including_revoked,
    issue_refresh_token,
    revoke_all_sessions,
    revoke_session,
    rotate_refresh_token,
    sign_access_token,
)

VERIFY_TTL = timedelta(hours=24)

# Brute-force throttle: lock an (tenant,email) after N failures within the window.
LOGIN_MAX_FAILS = 10
LOGIN_FAIL_WINDOW_S = 900  # 15 minutes


@dataclass
class AuthCtx:
    ip: str | None
    user_agent: str | None


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    user_id: str
    tenant_id: str


# --------------------------------------------------------------------------
# Brute-force defense (fails OPEN on Redis errors so a cache outage cannot
# lock everyone out). Two independent counters:
#   * captcha counter, keyed by (tenant, email): drives the captcha step-up.
#     Adding a captcha is friction, not a lockout, so it can't be weaponized.
#   * hard-lock counter, keyed by (tenant, email, IP): drives the 429 lock.
#     Keying by IP means an attacker can only lock THEIR OWN path, never freeze
#     a victim who logs in from a different IP (no targeted account-lockout DoS).
# --------------------------------------------------------------------------
def _captcha_key(tenant_id: str, email: str) -> str:
    return f"login_fail:{tenant_id}:{sha256(email)}"


def _lock_key(tenant_id: str, email: str, ip: str | None) -> str:
    return f"login_lock:{tenant_id}:{sha256(email)}:{sha256(ip or 'noip')}"


async def _get_count(key: str) -> int:
    try:
        raw = await redis_client.get(key)
    except Exception as err:  # noqa: BLE001 - fail open
        logger.warning("login throttle read failed open", error_message=str(err))
        return 0
    return int(raw) if raw is not None else 0


async def _incr(key: str) -> None:
    try:
        if await redis_client.incr(key) == 1:
            await redis_client.expire(key, LOGIN_FAIL_WINDOW_S)
    except Exception as err:  # noqa: BLE001 - fail open
        logger.warning("login throttle write failed open", error_message=str(err))


async def _record_failure(tenant_id: str, email: str, ip: str | None) -> None:
    await _incr(_captcha_key(tenant_id, email))
    await _incr(_lock_key(tenant_id, email, ip))


async def _clear_failures(tenant_id: str, email: str, ip: str | None) -> None:
    try:
        await redis_client.delete(_captcha_key(tenant_id, email), _lock_key(tenant_id, email, ip))
    except Exception as err:  # noqa: BLE001
        logger.warning("login throttle clear failed open", error_message=str(err))


# --------------------------------------------------------------------------
async def _dispatch_verification(user_id: str, email: str, tenant_id: str) -> None:
    raw = random_token(32)
    await db.execute(
        """INSERT INTO email_verification_tokens (user_id, tenant_id, token_hash, purpose, expires_at)
           VALUES ($1, $2, $3, 'verify_email', $4)""",
        user_id,
        tenant_id,
        sha256(raw),
        datetime.now(UTC) + VERIFY_TTL,
    )
    # A mail-provider blip must not fail signup (the account exists; the user
    # recovers via POST /auth/resend-verification). Log loudly and move on.
    try:
        await send_mail(build_verification_email(email, raw))
    except Exception as err:  # noqa: BLE001
        logger.error("verification email failed; user can resend", user_id=user_id, error_message=str(err))


async def resend_verification(*, email: str, tenant_id: str | None, captcha_token: str | None, ctx: AuthCtx) -> None:
    """Re-issue a verification email. Anti-enumeration: callers always get the
    same generic response whether or not the account exists / is verified."""
    tenant = tenant_id or settings.default_tenant_id
    email_norm = email.lower().strip()
    if not await verify_turnstile(captcha_token, ctx.ip):
        raise ApiError("CAPTCHA_REQUIRED")

    async with db.with_tenant(tenant) as conn:
        row = await conn.fetchrow(
            "SELECT user_id, is_verified FROM users WHERE tenant_id = $1 AND email = $2", tenant, email_norm
        )
    if row is None or row["is_verified"]:
        return  # silent: don't reveal whether the account exists or its state

    await _dispatch_verification(str(row["user_id"]), email_norm, tenant)
    await audit("user.verification_resent", user_id=str(row["user_id"]), tenant_id=tenant,
                resource="user", resource_id=str(row["user_id"]), ip_address=ctx.ip)


async def signup(
    *,
    email: str,
    password: str,
    full_name: str | None,
    tenant_id: str | None,
    captcha_token: str | None,
    ctx: AuthCtx,
) -> str:
    tenant = tenant_id or settings.default_tenant_id
    email_norm = email.lower().strip()

    # Captcha is always required on signup (no-op when Turnstile is disabled).
    if not await verify_turnstile(captcha_token, ctx.ip):
        raise ApiError("CAPTCHA_REQUIRED")

    async with db.with_tenant(tenant) as conn:
        existing = await conn.fetchval(
            "SELECT user_id FROM users WHERE tenant_id = $1 AND email = $2", tenant, email_norm
        )
        if existing:
            raise ApiError("CONFLICT", message="An account with this email already exists.")
        # asyncpg returns uuid.UUID; normalize to str at the boundary.
        user_id = str(
            await conn.fetchval(
                """INSERT INTO users (tenant_id, email, password_hash, full_name)
                   VALUES ($1, $2, $3, $4) RETURNING user_id""",
                tenant,
                email_norm,
                hash_password(password),
                full_name,
            )
        )

    # notification_preferences is now FORCE-RLS (migration 008) — write it inside
    # the tenant context with its tenant_id.
    async with db.with_tenant(tenant) as conn:
        await conn.execute(
            "INSERT INTO notification_preferences (user_id, tenant_id) VALUES ($1, $2)", user_id, tenant
        )
    await _dispatch_verification(user_id, email_norm, tenant)
    await audit(
        "user.signup", user_id=user_id, tenant_id=tenant, resource="user", resource_id=user_id, ip_address=ctx.ip
    )
    return user_id


async def verify_email(raw_token: str) -> None:
    # Token lookup is secret-keyed (cross-tenant by nature); carries tenant_id.
    row = await db.fetchrow(
        """SELECT token_id, user_id, tenant_id FROM email_verification_tokens
            WHERE token_hash = $1 AND purpose = 'verify_email'
              AND consumed_at IS NULL AND expires_at > NOW()""",
        sha256(raw_token),
    )
    if not row:
        raise ApiError("VALIDATION_ERROR", message="Invalid or expired verification token.")

    await db.execute("UPDATE email_verification_tokens SET consumed_at = NOW() WHERE token_id = $1", row["token_id"])
    async with db.with_tenant(str(row["tenant_id"])) as conn:
        await conn.execute("UPDATE users SET is_verified = true WHERE user_id = $1", row["user_id"])
    await audit("user.email_verified", user_id=str(row["user_id"]), resource="user", resource_id=str(row["user_id"]))


async def login(
    *, email: str, password: str, tenant_id: str | None, captcha_token: str | None, ctx: AuthCtx
) -> TokenPair:
    tenant = tenant_id or settings.default_tenant_id
    email_norm = email.lower().strip()

    # Hard lock is per-IP (can't be used to freeze a victim from elsewhere).
    if await _get_count(_lock_key(tenant, email_norm, ctx.ip)) >= LOGIN_MAX_FAILS:
        raise ApiError("RATE_LIMITED")
    # Captcha step-up is per-email (stops distributed bot guessing) — friction
    # only, never a lockout, so it can't be weaponized for DoS.
    captcha_fails = await _get_count(_captcha_key(tenant, email_norm))
    if captcha_fails >= settings.login_captcha_after_fails and not await verify_turnstile(captcha_token, ctx.ip):
        raise ApiError("CAPTCHA_REQUIRED")

    async with db.with_tenant(tenant) as conn:
        user = await conn.fetchrow(
            "SELECT user_id, tenant_id, password_hash, tier FROM users WHERE tenant_id = $1 AND email = $2",
            tenant,
            email_norm,
        )

    # Always spend ~equal CPU whether or not the account exists (anti-enumeration).
    if user is not None:
        ok = verify_password(password, user["password_hash"])
    else:
        verify_password(password, DUMMY_PASSWORD_HASH)
        ok = False

    if user is None or not ok:
        await _record_failure(tenant, email_norm, ctx.ip)
        await audit(
            "user.login_failed",
            tenant_id=tenant,
            resource="user",
            ip_address=ctx.ip,
            metadata={"email_present": user is not None},
        )
        raise ApiError("UNAUTHORIZED", message="Invalid email or password.")

    await _clear_failures(tenant, email_norm, ctx.ip)
    pair = await _issue_pair(str(user["user_id"]), str(user["tenant_id"]), user["tier"], ctx)
    async with db.with_tenant(tenant) as conn:
        await conn.execute("UPDATE users SET last_login_at = NOW() WHERE user_id = $1", user["user_id"])
    await audit(
        "user.login",
        user_id=str(user["user_id"]),
        tenant_id=tenant,
        resource="user",
        resource_id=str(user["user_id"]),
        ip_address=ctx.ip,
    )
    return pair


async def refresh(raw_refresh_token: str, ctx: AuthCtx) -> TokenPair:
    session = await find_live_session(raw_refresh_token)
    if not session:
        # Reuse detection: if this token exists but was already revoked, it was
        # rotated away — a replay of an old token signals theft. Revoke the
        # whole family so neither attacker nor victim keeps a usable session.
        stale = await find_session_including_revoked(raw_refresh_token)
        if stale and stale["revoked_at"] is not None:
            await revoke_all_sessions(str(stale["user_id"]))
            await audit(
                "session.reuse_detected",
                user_id=str(stale["user_id"]),
                tenant_id=str(stale["tenant_id"]),
                resource="session",
                ip_address=ctx.ip,
            )
        raise ApiError("UNAUTHORIZED", message="Invalid or expired session.")

    tenant = str(session["tenant_id"])
    async with db.with_tenant(tenant) as conn:
        user = await conn.fetchrow("SELECT user_id, tenant_id, tier FROM users WHERE user_id = $1", session["user_id"])
    if not user:
        raise ApiError("UNAUTHORIZED")

    new_refresh = await rotate_refresh_token(
        str(session["session_id"]), str(user["user_id"]), str(user["tenant_id"]), ctx.ip, ctx.user_agent
    )
    access = sign_access_token(str(user["user_id"]), str(user["tenant_id"]), user["tier"])
    await audit(
        "session.refresh",
        user_id=str(user["user_id"]),
        tenant_id=str(user["tenant_id"]),
        resource="session",
        resource_id=str(session["session_id"]),
        ip_address=ctx.ip,
    )
    return TokenPair(access, new_refresh, str(user["user_id"]), str(user["tenant_id"]))


async def logout(raw_refresh_token: str | None) -> None:
    if raw_refresh_token:
        await revoke_session(raw_refresh_token)


async def _issue_pair(user_id: str, tenant_id: str, tier: str, ctx: AuthCtx) -> TokenPair:
    access = sign_access_token(user_id, tenant_id, tier)
    refresh_token = await issue_refresh_token(user_id, tenant_id, ctx.ip, ctx.user_agent)
    return TokenPair(access, refresh_token, user_id, tenant_id)
