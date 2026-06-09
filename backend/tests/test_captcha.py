"""Captcha verifier behavior (no live Cloudflare call)."""
from __future__ import annotations

import app.captcha as captcha
from app.captcha import verify_turnstile


async def test_disabled_is_noop_and_allows() -> None:
    # Default test config: turnstile disabled -> always passes (even with no token).
    assert await verify_turnstile(None) is True
    assert await verify_turnstile("anything") is True


async def test_enabled_without_secret_fails_closed(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(captcha.settings, "turnstile_enabled", True)
    monkeypatch.setattr(captcha.settings, "turnstile_secret_key", None)
    assert await verify_turnstile("token") is False


async def test_enabled_missing_token_fails_closed(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(captcha.settings, "turnstile_enabled", True)
    monkeypatch.setattr(captcha.settings, "turnstile_secret_key", "secret")
    assert await verify_turnstile(None) is False
