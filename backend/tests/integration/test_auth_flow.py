"""End-to-end auth flow against real Postgres + Redis via the ASGI app."""
from __future__ import annotations

import time

import httpx
import pytest

from app.config import settings
from tests.integration.auth_helpers import DEFAULT_PASSWORD, login_as_user, login_via_magic_link
from tests.integration.conftest import _db_reachable

pytestmark = pytest.mark.skipif(not _db_reachable(), reason="Postgres not reachable on localhost:5433")


async def test_signup_login_me_and_wrong_password(client: httpx.AsyncClient) -> None:
    if settings.auth_mode != "password":
        pytest.skip("password-mode test")

    email = f"it+{int(time.time()*1000)}@example.com"
    pw = DEFAULT_PASSWORD

    r = await client.post("/api/v1/auth/signup", json={"email": email, "password": pw})
    assert r.status_code == 201, r.text
    assert isinstance(r.json()["user_id"], str)

    r = await client.post("/api/v1/auth/signup", json={"email": email, "password": pw})
    assert r.status_code == 409

    token = await login_as_user(client, email, pw)

    r = await client.get("/api/v1/auth/me", headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == email

    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401
    assert r.json()["code"] == "UNAUTHORIZED"

    r = await client.post("/api/v1/auth/login", json={"email": email, "password": "nope"})
    assert r.status_code == 401


async def test_magic_link_login_and_me(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "auth_mode", "magic_link")
    email = f"it+ml{int(time.time()*1000)}@example.com"

    token = await login_via_magic_link(client, email)

    r = await client.get("/api/v1/auth/me", headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == email
    assert r.json()["is_verified"] is True


async def test_magic_link_is_generic_for_unknown_email(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "auth_mode", "magic_link")
    email = f"it+known{int(time.time()*1000)}@example.com"
    r_known = await client.post("/api/v1/auth/magic-link", json={"email": email})
    assert r_known.status_code == 200

    r_unknown = await client.post(
        "/api/v1/auth/magic-link", json={"email": f"nobody{int(time.time()*1000)}@example.com"}
    )
    assert r_unknown.status_code == 200
    assert r_known.json()["message"] == r_unknown.json()["message"]


async def test_auth_mode_guards(client: httpx.AsyncClient) -> None:
    if settings.auth_mode == "password":
        r = await client.post("/api/v1/auth/magic-link", json={"email": "x@y.com"})
        assert r.status_code == 404
    else:
        r = await client.post("/api/v1/auth/login", json={"email": "x@y.com", "password": "x"})
        assert r.status_code == 404


async def test_auth_config_endpoint(client: httpx.AsyncClient) -> None:
    r = await client.get("/api/v1/auth/config")
    assert r.status_code == 200
    assert r.json()["auth_mode"] == settings.auth_mode


async def test_security_headers_present(client: httpx.AsyncClient) -> None:
    r = await client.get("/health")
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"
    assert r.headers.get("referrer-policy") == "no-referrer"
    assert r.headers.get("cache-control") == "no-store"


async def test_validation_error_shape(client: httpx.AsyncClient) -> None:
    if settings.auth_mode == "password":
        r = await client.post("/api/v1/auth/signup", json={"email": "not-an-email", "password": "x"})
    else:
        r = await client.post("/api/v1/auth/magic-link", json={"email": "not-an-email"})
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "request_id" in body


async def test_validation_error_does_not_leak_password(client: httpx.AsyncClient) -> None:
    if settings.auth_mode != "password":
        pytest.skip("password-mode test")

    secret = "superSecretPasswordThatMustNotBeEchoed"
    r = await client.post("/api/v1/auth/signup", json={"email": "x@y.com", "password": secret[:3]})
    assert r.status_code == 422
    assert secret[:3] not in r.text
    assert "input" not in r.text


async def test_extra_fields_rejected(client: httpx.AsyncClient) -> None:
    if settings.auth_mode == "password":
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "x@y.com", "password": "whatever123", "is_admin": True},
        )
    else:
        r = await client.post(
            "/api/v1/auth/magic-link",
            json={"email": "x@y.com", "is_admin": True},
        )
    assert r.status_code == 422


async def test_resend_verification_is_generic_for_all_states(client: httpx.AsyncClient) -> None:
    if settings.auth_mode != "password":
        pytest.skip("password-mode test")

    try:
        from app.redis_client import redis_client

        async for key in redis_client.scan_iter("rl:auth_resend:*"):
            await redis_client.delete(key)
    except Exception:  # noqa: BLE001 - test hygiene
        pass

    email = f"it+resend{int(time.time()*1000)}@example.com"
    r = await client.post("/api/v1/auth/signup", json={"email": email, "password": DEFAULT_PASSWORD})
    assert r.status_code == 201

    r_existing = await client.post("/api/v1/auth/resend-verification", json={"email": email})
    r_unknown = await client.post(
        "/api/v1/auth/resend-verification", json={"email": f"nobody{int(time.time()*1000)}@example.com"}
    )
    assert r_existing.status_code == 200
    assert r_unknown.status_code == 200
    assert r_existing.json()["message"] == r_unknown.json()["message"]
