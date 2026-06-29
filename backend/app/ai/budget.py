"""Per-user daily token usage accounting (no enforcement cap)."""
from __future__ import annotations

from app import db


async def record_usage(user_id: str, tenant_id: str, actual_tokens: int, provider: str) -> None:
    """Increment today's token counter after a completed advisor turn."""
    if actual_tokens <= 0:
        return
    async with db.with_tenant(tenant_id, user_id) as conn:
        await conn.execute(
            """INSERT INTO token_usage (user_id, tenant_id, date, tokens, provider)
               VALUES ($1, $2, CURRENT_DATE, $3, $4)
               ON CONFLICT (user_id, date)
               DO UPDATE SET tokens = token_usage.tokens + EXCLUDED.tokens, provider = EXCLUDED.provider""",
            user_id, tenant_id, actual_tokens, provider,
        )
