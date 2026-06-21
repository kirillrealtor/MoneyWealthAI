"""Email transport abstraction.

In dev (MAIL_TRANSPORT=console) we log the link instead of sending. Real
transports: `smtp` (any provider — Gmail, Amazon SES SMTP endpoint, Mailgun)
and `sendgrid` (HTTP API). Callers never change when the transport does.

SECURITY: real transports never log the message body — verification emails
contain a live token; only the console transport (dev) prints it.
"""
from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
from urllib.parse import quote

import httpx

from app.config import settings
from app.logging_conf import logger


class MailDeliveryError(Exception):
    """Transport-level send failure. Callers decide whether it's fatal."""


@dataclass
class Mail:
    to: str
    subject: str
    text: str


async def send_mail(mail: Mail) -> None:
    if settings.mail_transport == "console":
        logger.info("DEV email (not sent)", service="mailer", subject=mail.subject, dev_to=mail.to, body=mail.text)
        return
    try:
        if settings.mail_transport == "smtp":
            await _send_smtp(mail)
        else:  # sendgrid (validated at startup)
            await _send_sendgrid(mail)
    except MailDeliveryError:
        raise
    except Exception as err:
        logger.error("email send failed", service="mailer", transport=settings.mail_transport,
                     subject=mail.subject, error_message=str(err))
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
        # Don't include the response body in the exception by default — keep
        # provider error details in logs only.
        logger.error("sendgrid rejected message", service="mailer", status=resp.status_code,
                     error_message=resp.text[:500])
        raise MailDeliveryError(f"sendgrid status {resp.status_code}")


def build_verification_email(to: str, token: str) -> Mail:
    # Link points at the FRONTEND verify-email page (web_app_url), which posts the
    # token back via the BFF and shows a proper "verified" screen — not raw API JSON.
    url = f"{settings.web_app_url}/verify-email?token={quote(token, safe='')}"
    return Mail(
        to=to,
        subject="Verify your email",
        text=f"Welcome! Confirm your email to activate your account:\n\n{url}\n\nThis link expires in 24 hours.",
    )


def build_reset_email(to: str, token: str) -> Mail:
    # Reset link points at the FRONTEND page (web_app_url), which posts the token back.
    url = f"{settings.web_app_url}/reset-password?token={quote(token, safe='')}"
    return Mail(
        to=to,
        subject="Reset your password",
        text=(
            "We received a request to reset your MoneyWealth AI password. Click below to choose a new one:"
            f"\n\n{url}\n\nThis link expires in 1 hour. If you didn't request this, ignore this email."
        ),
    )
