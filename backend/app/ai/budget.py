"""Per-tier daily token budgets — the cost-control valve at 1M-user scale.

Atomic reserve-then-settle (no TOCTOU): the gate INCREMENTS the daily counter
and checks the returned total in a single statement, so two concurrent turns
can't both slip past a near-limit check. A conservative estimate is reserved
up front and reconciled to the real token count after the turn.
"""
from __future__ import annotations

from app import db
from app.config import settings
from app.errors import ApiError

# Conservative per-turn reservation (input context + max output + a tool round).
RESERVE_ESTIMATE = 5000


async def reserve_budget(user_id: str, tenant_id: str, tier: str) -> None:
    """Atomically reserve this turn's estimated tokens; raise if it would exceed
    today's budget (and refund the reservation so it isn't double-counted)."""
    limit = settings.token_budget_for(tier)
    async with db.with_tenant(tenant_id) as conn:
        total = await conn.fetchval(
            """INSERT INTO token_usage (user_id, tenant_id, date, tokens)
               VALUES ($1, $2, CURRENT_DATE, $3)
               ON CONFLICT (user_id, date)
               DO UPDATE SET tokens = token_usage.tokens + EXCLUDED.tokens
               RETURNING tokens""",
            user_id, tenant_id, RESERVE_ESTIMATE,
        )
        if int(total) > limit:
            await conn.execute(
                "UPDATE token_usage SET tokens = tokens - $1 WHERE user_id = $2 AND date = CURRENT_DATE",
                RESERVE_ESTIMATE, user_id,
            )
            raise ApiError("RATE_LIMITED", message="Daily AI usage limit reached. Upgrade for more.")


async def settle_usage(user_id: str, tenant_id: str, actual_tokens: int, provider: str) -> None:
    """Reconcile the reservation to the real token count (delta may be negative)."""
    delta = actual_tokens - RESERVE_ESTIMATE
    async with db.with_tenant(tenant_id) as conn:
        await conn.execute(
            """INSERT INTO token_usage (user_id, tenant_id, date, tokens, provider)
               VALUES ($1, $2, CURRENT_DATE, $3, $4)
               ON CONFLICT (user_id, date)
               DO UPDATE SET tokens = token_usage.tokens + EXCLUDED.tokens, provider = EXCLUDED.provider""",
            user_id, tenant_id, delta, provider,
        )
