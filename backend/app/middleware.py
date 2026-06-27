"""HTTP middleware: per-request trace context + access logging."""
from __future__ import annotations

import json
import time
import uuid
from collections.abc import MutableMapping
from typing import Any

from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import settings
from app.context import RequestContext, set_context
from app.logging_conf import logger

# ALB/ECS liveness probes hit these with Host = the task IP, not the public API name.
_HEALTH_PROBE_PATHS = frozenset({"/health", "/health/ready"})


class HealthExemptTrustedHostMiddleware:
    """TrustedHostMiddleware that skips probe paths (ALB uses task IP as Host)."""

    def __init__(self, app: ASGIApp, allowed_hosts: list[str]) -> None:
        self.app = app
        self._trusted = TrustedHostMiddleware(app, allowed_hosts=allowed_hosts)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope.get("path") in _HEALTH_PROBE_PATHS:
            await self.app(scope, receive, send)
            return
        await self._trusted(scope, receive, send)


class TracingMiddleware:
    """Establishes a RequestContext (trace_id) for every request and logs the
    response. Pure-ASGI so the contextvar is set in the same task that runs the
    handler (Architecture 19.2).
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode(): v.decode() for k, v in scope.get("headers", [])}
        trace_id = headers.get("x-trace-id") or str(uuid.uuid4())
        set_context(RequestContext(trace_id=trace_id))
        start = time.monotonic()
        status_holder = {"code": 0}

        async def send_wrapper(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start":
                status_holder["code"] = message["status"]
                message.setdefault("headers", []).append((b"x-trace-id", trace_id.encode()))
            await send(message)

        await self.app(scope, receive, send_wrapper)
        logger.info(
            "request completed",
            service="api",
            method=scope.get("method"),
            path=scope.get("path"),
            status_code=status_holder["code"],
            latency_ms=int((time.monotonic() - start) * 1000),
        )


_SECURITY_HEADERS: list[tuple[bytes, bytes]] = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
    (b"cross-origin-opener-policy", b"same-origin"),
    (b"cross-origin-resource-policy", b"same-origin"),
    (b"x-permitted-cross-domain-policies", b"none"),
    (b"permissions-policy", b"geolocation=(), microphone=(), camera=()"),
    (b"cache-control", b"no-store"),
]


class SecurityMiddleware:
    """Defense-in-depth HTTP hardening:
      * rejects bodies larger than max_body_bytes (413) before they are buffered
      * sets standard security headers (incl. HSTS in production) on every response
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._headers = list(_SECURITY_HEADERS)
        if settings.is_prod:
            self._headers.append(
                (b"strict-transport-security", b"max-age=63072000; includeSubDomains; preload")
            )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        content_length = headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > settings.max_body_bytes:
            body = json.dumps(
                {"code": "PAYLOAD_TOO_LARGE", "message": "Request body exceeds the maximum allowed size."}
            ).encode()
            await send({
                "type": "http.response.start",
                "status": 413,
                "headers": [(b"content-type", b"application/json"), *self._headers],
            })
            await send({"type": "http.response.body", "body": body})
            return

        async def send_wrapper(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start":
                existing = message.get("headers", [])
                message["headers"] = [*existing, *self._headers]
            await send(message)

        await self.app(scope, receive, send_wrapper)
