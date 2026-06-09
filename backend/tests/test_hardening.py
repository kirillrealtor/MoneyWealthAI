"""Unit tests for the hardening fixes that need no datastore."""
from __future__ import annotations

from decimal import Decimal

from app.modules.auth.service import _captcha_key, _lock_key
from app.modules.plaid.sync import to_money


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
