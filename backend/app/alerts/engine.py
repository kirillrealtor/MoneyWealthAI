"""Alert engine: run every check for one user and dispatch results. The unit of
work is a single user — so a scheduler can fan this out across an SQS worker
fleet at 1M-user scale (each message = one user / one batch)."""
from __future__ import annotations

from app.logging_conf import logger
from app.notifications.dispatch import send_notification
from app.notifications.preferences import load_preferences

from .checks import check_budgets, check_goals, check_unusual_transactions


async def run_alerts_for_user(user_id: str, tenant_id: str) -> int:
    """Run all checks for one user; return the count of notifications dispatched."""
    prefs = await load_preferences(user_id, tenant_id)
    specs = []
    for check in (check_budgets, check_goals, check_unusual_transactions):
        try:
            specs += await check(user_id, tenant_id)
        except Exception as err:  # noqa: BLE001 - one bad check shouldn't sink the rest
            logger.error("alert check failed", service="alert-engine", check=check.__name__,
                         user_id=user_id, error_message=str(err))

    sent = 0
    for spec in specs:
        try:
            if await send_notification(user_id, tenant_id, spec, prefs):
                sent += 1
        except Exception as err:  # noqa: BLE001
            logger.error("alert dispatch failed", service="alert-engine", type=spec.type,
                         user_id=user_id, error_message=str(err))
    return sent
