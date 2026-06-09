"""Email transport abstraction.

In dev (MAIL_TRANSPORT=console) we log the link instead of sending. In
production this is swapped for SES/SendGrid without touching callers.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from app.config import settings
from app.logging_conf import logger


@dataclass
class Mail:
    to: str
    subject: str
    text: str


async def send_mail(mail: Mail) -> None:
    if settings.mail_transport == "console":
        logger.info("DEV email (not sent)", service="mailer", subject=mail.subject, dev_to=mail.to, body=mail.text)
        return
    # TODO(Phase 5): implement SES/SendGrid transport.
    logger.warning("mail transport not implemented; dropping", service="mailer", subject=mail.subject)


def build_verification_email(to: str, token: str) -> Mail:
    url = f"{settings.app_base_url}/api/v1/auth/verify-email?token={quote(token)}"
    return Mail(
        to=to,
        subject="Verify your email",
        text=f"Welcome! Confirm your email to activate your account:\n\n{url}\n\nThis link expires in 24 hours.",
    )
