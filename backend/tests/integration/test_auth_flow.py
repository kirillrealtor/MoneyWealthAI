"""End-to-end auth flow against real Postgres + Redis via the ASGI app."""
from __future__ import annotations

import time

import httpx
import pytest

from tests.integration.conftest import _db_reachable

pytestmark = pytest.mark.skipif(not _db_reachable(), reason="Postgres not reachable on localhost:5433")


async def test_signup_login_me_and_wrong_password(client: httpx.AsyncClient) -> None:
    email = f"it+{int(time.time()*1000)}@example.com"
    pw = "SecurePass123!"

    r = await client.post("/api/v1/auth/signup", json={"email": email, "password": pw})
    assert r.status_code == 201, r.text
    assert isinstance(r.json()["user_id"], str)

    # duplicate -> 409
    r = await client.post("/api/v1/auth/signup", json={"email": email, "password": pw})
    assert r.status_code == 409

    # login -> 200 + token
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    # /me with token works and is RLS-scoped (returns the right user)
    r = await client.get("/api/v1/auth/me", headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == email

    # /me without token -> standardized 401
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401
    assert r.json()["code"] == "UNAUTHORIZED"

    # wrong password -> 401
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": "nope"})
    assert r.status_code == 401


async def test_security_headers_present(client: httpx.AsyncClient) -> None:
    r = await client.get("/health")
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"
    assert r.headers.get("referrer-policy") == "no-referrer"
    assert r.headers.get("cache-control") == "no-store"


async def test_validation_error_shape(client: httpx.AsyncClient) -> None:
    r = await client.post("/api/v1/auth/signup", json={"email": "not-an-email", "password": "x"})
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "request_id" in body


async def test_validation_error_does_not_leak_password(client: httpx.AsyncClient) -> None:
    secret = "superSecretPasswordThatMustNotBeEchoed"
    r = await client.post("/api/v1/auth/signup", json={"email": "x@y.com", "password": secret[:3]})
    # Too-short password fails validation; the raw input must NOT appear anywhere.
    assert r.status_code == 422
    assert secret[:3] not in r.text
    assert "input" not in r.text  # the leaky Pydantic field is stripped


async def test_extra_fields_rejected(client: httpx.AsyncClient) -> None:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "x@y.com", "password": "whatever123", "is_admin": True},
    )
    assert r.status_code == 422  # extra="forbid" rejects unexpected fields
