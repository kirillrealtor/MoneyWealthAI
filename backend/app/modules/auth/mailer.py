"""Email transport abstraction.

In dev (MAIL_TRANSPORT=console) we log the link instead of sending. Real
transports: `smtp`, `sendgrid`, `resend`. Callers never change when the
transport does.

SECURITY: real transports never log the message body — verification emails
contain a live token; only the console transport (dev) prints it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from email.message import EmailMessage
from urllib.parse import quote

import httpx

from app.config import settings
from app.logging_conf import logger


@dataclass
class Mail:
    to: str
    subject: str
    text: str


# Dev/test outbox — last N sent mails retained for E2E token extraction (non-prod).
_MAIL_OUTBOX: list[Mail] = []
_OUTBOX_MAX = 50


class MailDeliveryError(Exception):
    """Transport-level send failure. Callers decide whether it's fatal."""


def peek_last_mail_to(email: str) -> Mail | None:
    """Return the most recent mail sent to `email` (dev/E2E helper)."""
    norm = email.lower().strip()
    for mail in reversed(_MAIL_OUTBOX):
        if mail.to.lower().strip() == norm:
            return mail
    return None


def extract_magic_link_token(mail: Mail) -> str | None:
    """Parse the raw token from a magic-link email body."""
    m = re.search(r"/verify-email\?token=([^ \n\r]+)", mail.text)
    if not m:
        return None
    from urllib.parse import unquote

    return unquote(m.group(1))


async def send_mail(mail: Mail) -> None:
    _MAIL_OUTBOX.append(mail)
    if len(_MAIL_OUTBOX) > _OUTBOX_MAX:
        del _MAIL_OUTBOX[: len(_MAIL_OUTBOX) - _OUTBOX_MAX]

    if settings.mail_transport == "console":
        logger.info("DEV email (not sent)", service="mailer", subject=mail.subject, dev_to=mail.to, body=mail.text)
        return
    try:
        if settings.mail_transport == "smtp":
            await _send_smtp(mail)
        elif settings.mail_transport == "sendgrid":
            await _send_sendgrid(mail)
        else:  # resend (validated at startup)
            await _send_resend(mail)
    except MailDeliveryError:
        raise
    except Exception as err:
        logger.error(
            "email send failed",
            service="mailer",
            transport=settings.mail_transport,
            subject=mail.subject,
            error_message=str(err),
        )
        raise MailDeliveryError(str(err)) from err
    logger.info("email sent", service="mailer", transport=settings.mail_transport, subject=mail.subject)


async def _send_smtp(mail: Mail) -> None:
    import aiosmtplib

    msg = EmailMessage()
    msg["From"] = settings.mail_from
    msg["To"] = mail.to
    msg["Subject"] = mail.subject
    msg.set_content(mail.text)
    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        start_tls=settings.smtp_starttls,
        timeout=15,
    )


async def _send_sendgrid(mail: Mail) -> None:
    payload = {
        "personalizations": [{"to": [{"email": mail.to}]}],
        "from": {"email": settings.mail_from},
        "subject": mail.subject,
        "content": [{"type": "text/plain", "value": mail.text}],
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=payload,
            headers={"Authorization": f"Bearer {settings.sendgrid_api_key}"},
        )
    if resp.status_code >= 300:
        logger.error(
            "sendgrid rejected message",
            service="mailer",
            status=resp.status_code,
            error_message=resp.text[:500],
        )
        raise MailDeliveryError(f"sendgrid status {resp.status_code}")


async def _send_resend(mail: Mail) -> None:
    payload = {
        "from": settings.mail_from,
        "to": [mail.to],
        "subject": mail.subject,
        "text": mail.text,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
        )
    if resp.status_code >= 300:
        detail = resp.text[:500]
        logger.error(
            "resend rejected message",
            service="mailer",
            status=resp.status_code,
            error_message=detail,
        )
        raise MailDeliveryError(f"resend status {resp.status_code}: {detail}")


def build_magic_link_email(to: str, token: str) -> Mail:
    # Link points at the FRONTEND verify-email page (web_app_url), which posts the
    # token back via the BFF and shows a proper "verified" screen — not raw API JSON.
    url = f"{settings.web_app_url}/verify-email?token={quote(token, safe='')}"
    ttl = settings.magic_link_ttl_minutes
    return Mail(
        to=to,
        subject="Sign in to MoneyWealth AI",
        text=(
            "Click the link below to sign in to your MoneyWealth AI account:\n\n"
            f"{url}\n\n"
            f"This link expires in {ttl} minutes and can only be used once. "
            "If you didn't request this, you can safely ignore this email."
        ),
    )


def build_verification_email(to: str, token: str) -> Mail:
    url = f"{settings.web_app_url}/verify-email?token={quote(token, safe='')}"
    return Mail(
        to=to,
        subject="Verify your email",
        text=f"Welcome! Confirm your email to activate your account:\n\n{url}\n\nThis link expires in 24 hours.",
    )


def build_reset_email(to: str, token: str) -> Mail:
    url = f"{settings.web_app_url}/reset-password?token={quote(token, safe='')}"
    return Mail(
        to=to,
        subject="Reset your password",
        text=(
            "We received a request to reset your MoneyWealth AI password. Click below to choose a new one:"
            f"\n\n{url}\n\nThis link expires in 1 hour. If you didn't request this, ignore this email."
        ),
    )
