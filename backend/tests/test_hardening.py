"""Unit tests for the hardening fixes that need no datastore."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.config import Settings
from app.modules.auth.service import _captcha_key, _lock_key
from app.modules.plaid.sync import to_money

_BASE_ENV = {
    "database_url": "postgres://u:p@localhost:5433/db",
    "redis_url": "redis://localhost:6380",
    "jwt_access_secret": "x" * 32,
    "jwt_refresh_secret": "y" * 32,
}


def test_prod_rejects_wildcard_allowed_hosts() -> None:
    with pytest.raises(ValueError, match="ALLOWED_HOSTS"):
        Settings(env="production", allowed_hosts="*", **_BASE_ENV)  # type: ignore[arg-type]


def test_prod_accepts_explicit_allowed_hosts() -> None:
    s = Settings(env="production", allowed_hosts="api.fathom.app,fathom.app", **_BASE_ENV)  # type: ignore[arg-type]
    assert "*" not in s.allowed_hosts_list


def test_dev_still_allows_wildcard_hosts() -> None:
    s = Settings(env="development", allowed_hosts="*", **_BASE_ENV)  # type: ignore[arg-type]
    assert s.allowed_hosts_list == ["*"]


def test_plaid_configured_with_sandbox_secret() -> None:
    s = Settings(
        plaid_sandbox_secret="sandbox-key",
        plaid_client_id="cid",
        plaid_enc_key="e" * 43,
        **_BASE_ENV,
    )  # type: ignore[arg-type]
    assert s.plaid_configured is True


def test_health_probe_bypasses_trusted_host() -> None:
    """ALB probes /health with Host = task IP; API routes stay protected."""
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    from app.middleware import HealthExemptTrustedHostMiddleware

    async def api(_request):  # type: ignore[no-untyped-def]
        return PlainTextResponse("api")

    async def health(_request):  # type: ignore[no-untyped-def]
        return PlainTextResponse("ok")

    starlette_app = Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route("/api/v1/x", api, methods=["GET"]),
        ]
    )
    wrapped = HealthExemptTrustedHostMiddleware(starlette_app, allowed_hosts=["api.example.com"])
    client = TestClient(wrapped)
    assert client.get("/health", headers={"Host": "10.0.1.99"}).status_code == 200
    assert client.get("/api/v1/x", headers={"Host": "api.example.com"}).status_code == 200
    assert client.get("/api/v1/x", headers={"Host": "evil.example.com"}).status_code == 400


def test_to_money_avoids_float_error() -> None:
    assert to_money("12.50") == Decimal("12.50")
    assert to_money(99) == Decimal("99")
    # 0.1 as a float is 0.1000000000000000055...; str() keeps the decimal value.
    assert to_money(0.1) == Decimal("0.1")
    assert to_money(None) is None


def test_hard_lock_key_is_per_ip_but_captcha_key_is_not() -> None:
    t, e = "tenant", "user@example.com"
    # Hard lock differs by IP -> an attacker from one IP can't lock a victim's
    # other-IP path (no targeted-lockout DoS).
    assert _lock_key(t, e, "1.1.1.1") != _lock_key(t, e, "2.2.2.2")
    # Captcha step-up is per (tenant,email) regardless of IP (stops distributed
    # guessing) but only adds friction, never a lockout.
    assert _captcha_key(t, e) == _captcha_key(t, e)
    assert _lock_key(t, e, None) == _lock_key(t, e, None)
