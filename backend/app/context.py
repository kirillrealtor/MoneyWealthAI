"""Per-request context propagated through async calls via contextvars.

Implements the distributed-tracing requirement (Architecture 19.2): a trace_id
threads through DB, logger, and tool execution without passing params around.
"""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass
class RequestContext:
    trace_id: str
    user_id: str | None = None
    tenant_id: str | None = None


_ctx: ContextVar[RequestContext | None] = ContextVar("request_context", default=None)


def set_context(ctx: RequestContext) -> None:
    _ctx.set(ctx)


def get_context() -> RequestContext | None:
    return _ctx.get()


def get_trace_id() -> str | None:
    ctx = _ctx.get()
    return ctx.trace_id if ctx else None
