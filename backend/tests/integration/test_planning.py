"""Budgets + Goals CRUD against SQLite via the ASGI app."""
from __future__ import annotations

import time

import httpx
import pytest

from tests.integration.conftest import _db_reachable

pytestmark = pytest.mark.skipif(not _db_reachable(), reason="SQLite is always reachable")


async def _auth(client: httpx.AsyncClient) -> dict[str, str]:
    email = f"plan+{int(time.time()*1000)}@example.com"
    await client.post("/api/v1/auth/signup", json={"email": email, "password": "SecurePass123!"})
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass123!"})
    return {"authorization": f"Bearer {r.json()['access_token']}"}


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
