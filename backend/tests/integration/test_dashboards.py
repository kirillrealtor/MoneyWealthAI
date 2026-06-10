"""Debt + Portfolio dashboards against real Postgres (RLS-scoped)."""
from __future__ import annotations

import time

import httpx
import pytest

from app import db
from app.config import settings
from app.encryption import encrypt
from tests.integration.conftest import _db_reachable

pytestmark = pytest.mark.skipif(not _db_reachable(), reason="Postgres not reachable on localhost:5433")
TENANT = settings.default_tenant_id


async def _seed(client: httpx.AsyncClient) -> dict[str, str]:
    email = f"dash+{int(time.time()*1000)}@example.com"
    r = await client.post("/api/v1/auth/signup", json={"email": email, "password": "SecurePass123!"})
    user_id = r.json()["user_id"]
    token = (await client.post("/api/v1/auth/login",
                               json={"email": email, "password": "SecurePass123!"})).json()["access_token"]
    enc = encrypt("access-sandbox", aad=user_id)
    async with db.with_tenant(TENANT) as conn:
        item_id = await conn.fetchval(
            """INSERT INTO plaid_items (user_id, tenant_id, plaid_item_id, access_token_enc, item_status)
               VALUES ($1,$2,$3,$4,'good') RETURNING item_id""",
            user_id, TENANT, f"it_{user_id}", enc)
        credit = await conn.fetchval(
            """INSERT INTO plaid_accounts (item_id, tenant_id, plaid_account_id, name, type, subtype, currency_code)
               VALUES ($1,$2,$3,'Card','credit','credit card','USD') RETURNING account_id""",
            item_id, TENANT, f"cc_{user_id}")
        invest = await conn.fetchval(
            """INSERT INTO plaid_accounts (item_id, tenant_id, plaid_account_id, name, type, subtype, currency_code)
               VALUES ($1,$2,$3,'Brokerage','investment','brokerage','USD') RETURNING account_id""",
            item_id, TENANT, f"inv_{user_id}")
        await conn.execute(
            """INSERT INTO debt_accounts (account_id, tenant_id, balance, apr, minimum_payment, debt_type)
               VALUES ($1,$2,'5000','0.2499','125','credit_card')""", credit, TENANT)
        await conn.execute(
            """INSERT INTO portfolio_holdings
                   (account_id, tenant_id, ticker, name, cost_basis, institution_value, asset_class, sector)
               VALUES ($1,$2,'AAPL','Apple','8000','10000','equity','Technology')""", invest, TENANT)
    return {"authorization": f"Bearer {token}"}


async def test_debt_dashboard(client: httpx.AsyncClient) -> None:
    h = await _seed(client)
    summary = (await client.get("/api/v1/debt", headers=h)).json()
    assert float(summary["total_debt"]) == 5000.0
    assert summary["debts"][0]["above_typical_rate"] is True  # 24.99% > 20% credit-card threshold
    assert summary["debts"][0]["months_at_minimum"] is not None

    payoff = (await client.post("/api/v1/debt/payoff", headers=h,
                                json={"extra_monthly_payment": "200"})).json()
    assert payoff["avalanche"]["months_to_payoff"] > 0
    assert float(payoff["interest_saved_with_avalanche"]) >= 0


async def test_portfolio_dashboard(client: httpx.AsyncClient) -> None:
    h = await _seed(client)
    summary = (await client.get("/api/v1/portfolio", headers=h)).json()
    assert float(summary["total_value"]) == 10000.0
    assert float(summary["unrealized_gain_loss"]) == 2000.0
    assert summary["allocation_pct"]["equity"] == 100.0
    # 100% in one sector and one holding -> concentration flagged.
    assert any("Technology" in f for f in summary["concentration_flags"])

    rebal = (await client.post("/api/v1/portfolio/rebalance", headers=h,
                               json={"target_allocation": {"equity": 60, "fixed_income": 40}})).json()
    gaps = {g["asset_class"]: g for g in rebal["gaps"]}
    assert gaps["equity"]["drift_pct"] == 40.0            # 100% current vs 60% target
    assert float(gaps["fixed_income"]["adjustment_value"]) == 4000.0  # add 40% of $10k


async def test_dashboards_require_auth(client: httpx.AsyncClient) -> None:
    assert (await client.get("/api/v1/debt")).status_code == 401
    assert (await client.get("/api/v1/portfolio")).status_code == 401
