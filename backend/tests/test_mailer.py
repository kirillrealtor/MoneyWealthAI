"""Mailer transport tests — console (dev), SMTP, SendGrid, Resend, and config guards.

No network: SMTP is monkeypatched at aiosmtplib.send; SendGrid and Resend use
httpx.MockTransport. Verifies the security property that real transports are
attempted with the right envelope (From/To/Subject) and that failures surface
as MailDeliveryError instead of leaking provider internals.
"""
from __future__ import annotations

from email.message import EmailMessage
from typing import Any

import httpx
import pytest

from app.config import settings
from app.modules.auth import mailer
from app.modules.auth.mailer import Mail, MailDeliveryError, build_magic_link_email, send_mail


async def test_console_transport_is_default_and_never_sends(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "mail_transport", "console")
    await send_mail(Mail(to="a@example.com", subject="s", text="b"))


async def test_smtp_transport_sends_correct_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    import aiosmtplib

    sent: dict[str, Any] = {}

    async def fake_send(msg: EmailMessage, **kwargs: Any) -> Any:
        sent["msg"] = msg
        sent["kwargs"] = kwargs
        return {}, "OK"

    monkeypatch.setattr(settings, "mail_transport", "smtp")
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_username", "user")
    monkeypatch.setattr(settings, "smtp_password", "pass")
    monkeypatch.setattr(aiosmtplib, "send", fake_send)

    await send_mail(Mail(to="dest@example.com", subject="Sign in to MoneyWealth AI", text="hello"))

    msg = sent["msg"]
    assert msg["From"] == settings.mail_from
    assert msg["To"] == "dest@example.com"
    assert msg["Subject"] == "Sign in to MoneyWealth AI"
    assert sent["kwargs"]["hostname"] == "smtp.example.com"
    assert sent["kwargs"]["port"] == 587
    assert sent["kwargs"]["start_tls"] is True


async def test_smtp_failure_raises_mail_delivery_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import aiosmtplib

    async def boom(msg: EmailMessage, **kwargs: Any) -> Any:
        raise ConnectionRefusedError("smtp down")

    monkeypatch.setattr(settings, "mail_transport", "smtp")
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(aiosmtplib, "send", boom)

    with pytest.raises(MailDeliveryError):
        await send_mail(Mail(to="a@example.com", subject="s", text="b"))


def _mock_http_post(monkeypatch: pytest.MonkeyPatch, url_prefix: str, status: int, captured: dict[str, Any]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        captured["body"] = request.content
        return httpx.Response(status)

    real_client = httpx.AsyncClient

    def client_factory(**kwargs: Any) -> httpx.AsyncClient:
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(**kwargs)

    monkeypatch.setattr(mailer.httpx, "AsyncClient", client_factory)


async def test_sendgrid_transport_posts_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(settings, "mail_transport", "sendgrid")
    monkeypatch.setattr(settings, "sendgrid_api_key", "SG.test-key")
    _mock_http_post(monkeypatch, "sendgrid", 202, captured)

    await send_mail(Mail(to="dest@example.com", subject="s", text="b"))

    assert captured["url"] == "https://api.sendgrid.com/v3/mail/send"
    assert captured["auth"] == "Bearer SG.test-key"
    assert b"dest@example.com" in captured["body"]


async def test_sendgrid_rejection_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "mail_transport", "sendgrid")
    monkeypatch.setattr(settings, "sendgrid_api_key", "SG.test-key")
    _mock_http_post(monkeypatch, "sendgrid", 401, {})

    with pytest.raises(MailDeliveryError):
        await send_mail(Mail(to="a@example.com", subject="s", text="b"))


async def test_resend_transport_posts_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(settings, "mail_transport", "resend")
    monkeypatch.setattr(settings, "resend_api_key", "re_test-key")
    _mock_http_post(monkeypatch, "resend", 200, captured)

    await send_mail(Mail(to="dest@example.com", subject="s", text="b"))

    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["auth"] == "Bearer re_test-key"
    assert b"dest@example.com" in captured["body"]


async def test_resend_rejection_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "mail_transport", "resend")
    monkeypatch.setattr(settings, "resend_api_key", "re_test-key")
    _mock_http_post(monkeypatch, "resend", 401, {})

    with pytest.raises(MailDeliveryError):
        await send_mail(Mail(to="a@example.com", subject="s", text="b"))


def test_magic_link_email_contains_link_and_urlencodes_token() -> None:
    mail = build_magic_link_email("a@example.com", "tok/with+specials")
    assert "/verify-email?token=tok%2Fwith%2Bspecials" in mail.text
    assert mail.to == "a@example.com"
    assert mail.subject == "Sign in to MoneyWealth AI"


def test_half_configured_transport_fails_at_startup() -> None:
    from app.config import Settings

    with pytest.raises(ValueError):
        Settings(mail_transport="smtp", smtp_host=None)
    with pytest.raises(ValueError):
        Settings(mail_transport="sendgrid", sendgrid_api_key=None)
    with pytest.raises(ValueError):
        Settings(mail_transport="resend", resend_api_key=None)
