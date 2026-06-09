"""Advisor orchestration against real Postgres with a mocked LLM provider:
proves the grounded tool loop, tenant-scoped executors, persistence, and token
accounting — without calling Anthropic."""
from __future__ import annotations

import time
from typing import Any

import httpx
import pytest

from app import db
from app.ai.advisor import run_turn
from app.ai.provider import AdvisorResult
from app.config import settings
from app.encryption import encrypt
from tests.integration.conftest import _db_reachable

pytestmark = pytest.mark.skipif(not _db_reachable(), reason="Postgres not reachable on localhost:5433")
TENANT = settings.default_tenant_id


class _FakeProvider:
    """Calls one tool, then returns a grounded, compliant final answer."""

    name = "fake"

    def __init__(self, tool: str, tool_input: dict[str, Any]) -> None:
        self._call = (tool, tool_input)
        self.tool_result: str | None = None

    async def run(self, *, system, messages, tools, execute_tool):  # type: ignore[no-untyped-def]
        tool, tool_input = self._call
        content, is_error = await execute_tool(tool, tool_input)
        self.tool_result = content
        return AdvisorResult(
            text="Based on your linked data, you spent $42.00 recently. Next, set a dining budget.",
            provider="fake", model="fake", tool_calls_made=[tool], input_tokens=100, output_tokens=50,
        )


async def _seed_user_with_spending(client: httpx.AsyncClient, amount: str = "42.00") -> str:
    email = f"advisor+{int(time.time()*1000)}@example.com"
    r = await client.post("/api/v1/auth/signup", json={"email": email, "password": "SecurePass123!"})
    user_id = r.json()["user_id"]
    token_enc = encrypt("access-sandbox", aad=user_id)
    async with db.with_tenant(TENANT) as conn:
        item_id = await conn.fetchval(
            """INSERT INTO plaid_items (user_id, tenant_id, plaid_item_id, access_token_enc, item_status)
               VALUES ($1,$2,$3,$4,'good') RETURNING item_id""",
            user_id, TENANT, f"it_{user_id}", token_enc,
        )
        acc_id = await conn.fetchval(
            """INSERT INTO plaid_accounts (item_id, tenant_id, plaid_account_id, name, type, subtype, currency_code)
               VALUES ($1,$2,$3,'Checking','depository','checking','USD') RETURNING account_id""",
            item_id, TENANT, f"acc_{user_id}",
        )
        await conn.execute(
            """INSERT INTO transactions (account_id, tenant_id, plaid_transaction_id, amount, date, category, pending)
               VALUES ($1,$2,$3,$4, CURRENT_DATE, 'FOOD_AND_DRINK', false)""",
            acc_id, TENANT, f"tx_{user_id}", amount,
        )
    return user_id


async def test_run_turn_grounds_persists_and_accounts(client: httpx.AsyncClient) -> None:
    user_id = await _seed_user_with_spending(client)
    provider = _FakeProvider("get_spending_summary", {"period": "last_30d"})

    result = await run_turn(
        user_id=user_id, tenant_id=TENANT, first_name="Test", persona="balanced", tier="free",
        chat_id=None, message="How much did I spend recently?", module="budget", provider=provider,
    )

    # The tool actually queried the user's own data (tenant-scoped) and saw $42.
    assert provider.tool_result is not None and "42" in provider.tool_result
    assert "$42.00" in result.response
    assert result.tool_calls_made == ["get_spending_summary"]

    # Persisted + accounted (read within tenant context — these tables are FORCE-RLS).
    async with db.with_tenant(TENANT) as conn:
        msgs = await conn.fetch(
            "SELECT role FROM chat_messages WHERE chat_id = $1 ORDER BY created_at", result.chat_id
        )
        used = await conn.fetchval(
            "SELECT tokens FROM token_usage WHERE user_id = $1 AND date = CURRENT_DATE", user_id
        )
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert int(used) == 150  # reserve 5000 then settle (150 - 5000) = net 150


async def test_crisis_message_bypasses_llm(client: httpx.AsyncClient) -> None:
    user_id = await _seed_user_with_spending(client)
    # Provider would raise if called — crisis path must not call it.
    result = await run_turn(
        user_id=user_id, tenant_id=TENANT, first_name="Test", persona="balanced", tier="free",
        chat_id=None, message="I can't afford rent and I'm going to lose my apartment", module=None, provider=None,
    )
    assert result.provider == "crisis_protocol"
    assert "NFCC" in result.response
    assert result.tokens_used == 0
