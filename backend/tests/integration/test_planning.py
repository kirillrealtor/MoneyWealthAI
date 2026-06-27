"""Budgets + Goals CRUD against real Postgres (RLS-scoped) via the ASGI app."""
from __future__ import annotations

import time

import httpx
import pytest

from tests.integration.auth_helpers import login_as_user
from tests.integration.conftest import _db_reachable

pytestmark = pytest.mark.skipif(not _db_reachable(), reason="Postgres not reachable on localhost:5433")


async def _auth(client: httpx.AsyncClient) -> dict[str, str]:
    email = f"plan+{int(time.time()*1000)}@example.com"
    token = await login_as_user(client, email)
    return {"authorization": f"Bearer {token}"}


async def test_budget_crud(client: httpx.AsyncClient) -> None:
    h = await _auth(client)
    r = await client.post("/api/v1/budgets", headers=h,
                          json={"category": "FOOD_AND_DRINK", "monthly_limit": "300"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["category"] == "FOOD_AND_DRINK" and float(body["monthly_limit"]) == 300
    bid = body["budget_id"]

    # duplicate category -> 409
    dup = await client.post("/api/v1/budgets", headers=h,
                            json={"category": "FOOD_AND_DRINK", "monthly_limit": "200"})
    assert dup.status_code == 409

    assert (await client.get("/api/v1/budgets", headers=h)).json()[0]["budget_id"] == bid
    assert (await client.patch(f"/api/v1/budgets/{bid}", headers=h, json={"monthly_limit": "400"})).status_code == 200
    assert (await client.delete(f"/api/v1/budgets/{bid}", headers=h)).status_code == 200
    assert (await client.get("/api/v1/budgets", headers=h)).json() == []


async def test_goal_create_reverse_engineers_target(client: httpx.AsyncClient) -> None:
    h = await _auth(client)
    r = await client.post("/api/v1/goals", headers=h, json={
        "title": "Emergency Fund", "target_amount": "12000", "current_amount": "0",
        "target_date": "2027-06-01",
    })
    assert r.status_code == 201, r.text
    goal = r.json()
    assert goal["title"] == "Emergency Fund"
    # A monthly target was reverse-engineered and progress reported.
    assert goal["monthly_target"] is not None and float(goal["monthly_target"]) > 0
    assert goal["progress_pct"] == 0.0

    gid = goal["goal_id"]
    # Contribute -> progress moves.
    await client.patch(f"/api/v1/goals/{gid}", headers=h, json={"current_amount": "6000"})
    updated = next(g for g in (await client.get("/api/v1/goals", headers=h)).json() if g["goal_id"] == gid)
    assert updated["progress_pct"] == 50.0


async def test_planning_requires_auth(client: httpx.AsyncClient) -> None:
    assert (await client.get("/api/v1/budgets")).status_code == 401
    assert (await client.get("/api/v1/goals")).status_code == 401


async def test_money_overflow_is_rejected_not_500(client: httpx.AsyncClient) -> None:
    """Pentest regression: a value exceeding NUMERIC(10,2) must 422 at the API,
    not reach the DB and raise an unhandled NumericValueOutOfRangeError (500)."""
    h = await _auth(client)
    over = await client.post("/api/v1/budgets", headers=h,
                             json={"category": "SHOPPING", "monthly_limit": "99999999999999999999"})
    assert over.status_code == 422
    # The exact ceiling is still accepted (valid Plaid category to isolate the
    # money bound from the category-enum check).
    at_cap = await client.post("/api/v1/budgets", headers=h,
                               json={"category": "ENTERTAINMENT", "monthly_limit": "99999999.99"})
    assert at_cap.status_code == 201, at_cap.text


async def test_goal_past_target_date_is_rejected(client: httpx.AsyncClient) -> None:
    """Pentest regression: a deadline in the past is meaningless and skews the
    monthly-target math — must be rejected."""
    h = await _auth(client)
    r = await client.post("/api/v1/goals", headers=h,
                          json={"title": "past", "target_amount": "1000", "target_date": "2000-01-01"})
    assert r.status_code == 422
    assert any(e["loc"][-1] == "target_date" for e in r.json()["details"])
