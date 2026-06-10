"""Channel adapters. Each is gated by config — unconfigured channels report
'not configured' so the dispatcher can skip them. In-app needs nothing (the
alerts row IS the in-app notification). Email reuses the pluggable mailer
(console in dev). Push (FCM) and SMS (Twilio) are stubs until keys are added."""
from __future__ import annotations

from app.logging_conf import logger
from app.modules.auth.mailer import Mail, send_mail


def is_configured(channel: str) -> bool:
    if channel == "email":
        return True  # console transport always "delivers" (logs) in dev
    if channel == "push":
        return False  # TODO(Phase 5): FCM
    if channel == "sms":
        return False  # TODO(Phase 5): Twilio (requires sms_opt_in / TCPA)
    return False


async def deliver(channel: str, *, to_email: str | None, title: str, body: str) -> bool:
    """Return True if delivered. Never raises into the dispatcher."""
    try:
        if channel == "email" and to_email:
            await send_mail(Mail(to=to_email, subject=title, text=body))
            return True
        return False
    except Exception as err:  # noqa: BLE001 - delivery failure is recorded in the outbox
        logger.warning("notification delivery failed", service="notifications", channel=channel, error_message=str(err))
        return False
