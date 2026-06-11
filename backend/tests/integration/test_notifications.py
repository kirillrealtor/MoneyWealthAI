"""Alert engine + in-app notification feed against SQLite + Redis."""
from __future__ import annotations

import time

import httpx
import pytest

from app import db
from app.alerts.engine import run_alerts_for_user
from app.config import settings
from app.encryption import encrypt
from tests.integration.conftest import _db_reachable

pytestmark = pytest.mark.skipif(not _db_reachable(), reason="SQLite is always reachable")
TENANT = settings.default_tenant_id


async def _seed_overspent_budget(client: httpx.AsyncClient) -> tuple[str, dict[str, str]]:
    email = f"notif+{int(time.time()*1000)}@example.com"
    user_id = (await client.post("/api/v1/auth/signup",
                                 json={"email": email, "password": "SecurePass123!"})).json()["user_id"]
    token = (await client.post("/api/v1/auth/login",
                               json={"email": email, "password": "SecurePass123!"})).json()["access_token"]
    h = {"authorization": f"Bearer {token}"}
    # $100 dining budget...
    await client.post("/api/v1/budgets", headers=h, json={"category": "FOOD_AND_DRINK", "monthly_limit": "100"})
    # ...and $150 of dining spend this month.
    enc = encrypt("access-sandbox", aad=user_id)
    async with db.with_tenant(TENANT) as conn:
        item_id = await conn.fetchval(
            """INSERT INTO plaid_items (user_id, tenant_id, plaid_item_id, access_token_enc, item_status)
               VALUES ($1,$2,$3,$4,'good') RETURNING item_id""", user_id, TENANT, f"it_{user_id}", enc)
        acc = await conn.fetchval(
            """INSERT INTO plaid_accounts (item_id, tenant_id, plaid_account_id, name, type, subtype, currency_code)
               VALUES ($1,$2,$3,'Card','depository','checking','USD') RETURNING account_id""",
            item_id, TENANT, f"acc_{user_id}")
        await conn.execute(
            """INSERT INTO transactions (account_id, tenant_id, plaid_transaction_id, amount, date, category, pending)
               VALUES ($1,$2,$3,'150', CURRENT_DATE, 'FOOD_AND_DRINK', false)""",
            acc, TENANT, f"tx_{user_id}")
    return user_id, h


async def test_budget_alert_fires_dedups_and_reads(client: httpx.AsyncClient) -> None:
    user_id, h = await _seed_overspent_budget(client)

    dispatched = await run_alerts_for_user(user_id, TENANT)
    assert dispatched >= 1

    feed = (await client.get("/api/v1/notifications", headers=h)).json()
    assert feed["unread_count"] >= 1
    budget_alerts = [n for n in feed["items"] if n["type"] == "budget_threshold"]
    assert budget_alerts and "FOOD_AND_DRINK" in budget_alerts[0]["title"]
    count_before = len(feed["items"])

    # Idempotent: re-running the scan must NOT create a duplicate.
    await run_alerts_for_user(user_id, TENANT)
    feed2 = (await client.get("/api/v1/notifications", headers=h)).json()
    assert len(feed2["items"]) == count_before

    # Mark read -> unread drops.
    aid = budget_alerts[0]["alert_id"]
    assert (await client.post(f"/api/v1/notifications/{aid}/read", headers=h)).status_code == 200
    assert (await client.get("/api/v1/notifications", headers=h)).json()["unread_count"] == feed["unread_count"] - 1


async def test_preferences_get_and_update(client: httpx.AsyncClient) -> None:
    _user_id, h = await _seed_overspent_budget(client)
    prefs = (await client.get("/api/v1/notifications/preferences", headers=h)).json()
    assert prefs["budget_alerts"] is True and prefs["sms_opt_in"] is False

    updated = (await client.patch("/api/v1/notifications/preferences", headers=h,
                                  json={"budget_alerts": False, "timezone": "America/New_York"})).json()
    assert updated["budget_alerts"] is False
    assert updated["timezone"] == "America/New_York"


async def test_notifications_require_auth(client: httpx.AsyncClient) -> None:
    assert (await client.get("/api/v1/notifications")).status_code == 401
    assert (await client.get("/api/v1/notifications/preferences")).status_code == 401
