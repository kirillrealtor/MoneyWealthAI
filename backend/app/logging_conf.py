"""Structured logging (Architecture 19.1).

Every line carries trace_id/user_id/tenant_id automatically from the request
context. PII SAFETY: never log email, phone, full_name, account numbers, access
tokens, or passwords. user_id (UUID) only.
"""
from __future__ import annotations

import logging
from typing import cast

import structlog
from structlog.typing import EventDict, Processor, WrappedLogger

from app.config import settings
from app.context import get_context

_SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "access_token",
    "access_token_enc",
    "email",
    "phone",
    "authorization",
    "cookie",
}


def _add_request_context(_logger: WrappedLogger, _name: str, event: EventDict) -> EventDict:
    ctx = get_context()
    if ctx:
        event.setdefault("trace_id", ctx.trace_id)
        if ctx.user_id:
            event.setdefault("user_id", ctx.user_id)
        if ctx.tenant_id:
            event.setdefault("tenant_id", ctx.tenant_id)
    return event


def _redact(_logger: WrappedLogger, _name: str, event: EventDict) -> EventDict:
    for key in list(event.keys()):
        if key in _SENSITIVE_KEYS:
            event[key] = "[redacted]"
    return event


def configure_logging() -> None:
    logging.basicConfig(level=settings.log_level.upper(), format="%(message)s")
    renderer: Processor = cast(
        Processor,
        structlog.processors.JSONRenderer() if settings.is_prod else structlog.dev.ConsoleRenderer(),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_request_context,
            _redact,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level.upper())
        ),
        cache_logger_on_first_use=True,
    )


logger = structlog.get_logger("app")
