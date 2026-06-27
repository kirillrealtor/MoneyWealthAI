"""Shared helpers for integration tests — auth mode aware."""
from __future__ import annotations

import httpx

from app.config import settings
from app.modules.auth.mailer import extract_magic_link_token, peek_last_mail_to

DEFAULT_PASSWORD = "SecurePass123!"


async def login_via_magic_link(client: httpx.AsyncClient, email: str) -> str:
    """Request a magic link, consume it, and return an access token."""
    r = await client.post("/api/v1/auth/magic-link", json={"email": email})
    assert r.status_code == 200, r.text

    mail = peek_last_mail_to(email)
    assert mail is not None, f"no magic link email captured for {email}"
    token = extract_magic_link_token(mail)
    assert token is not None, "could not parse magic link token from email"

    r = await client.get(f"/api/v1/auth/verify-email?token={token}")
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


async def login_via_password(
    client: httpx.AsyncClient, email: str, password: str = DEFAULT_PASSWORD
) -> str:
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


async def login_as_user(
    client: httpx.AsyncClient, email: str, password: str = DEFAULT_PASSWORD
) -> str:
    """Create/login a user using the active AUTH_MODE and return an access token."""
    if settings.auth_mode == "magic_link":
        return await login_via_magic_link(client, email)
    r = await client.post("/api/v1/auth/signup", json={"email": email, "password": password})
    if r.status_code not in (201, 409):
        raise AssertionError(r.text)
    return await login_via_password(client, email, password)


async def create_user(
    client: httpx.AsyncClient, email: str, password: str = DEFAULT_PASSWORD
) -> tuple[str, str]:
    """Create/login a user and return (user_id, access_token)."""
    access = await login_as_user(client, email, password)
    r = await client.get("/api/v1/auth/me", headers={"authorization": f"Bearer {access}"})
    assert r.status_code == 200, r.text
    return r.json()["user_id"], access


# Back-compat aliases used by existing tests.
create_user_via_magic_link = create_user
