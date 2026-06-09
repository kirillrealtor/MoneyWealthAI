"""Webhook verification rejects unsigned/malformed input (no live Plaid call)."""
from __future__ import annotations

import jwt

from app.modules.plaid.webhook import verify_webhook


async def test_missing_header_rejected() -> None:
    assert await verify_webhook(b'{"webhook_type":"TRANSACTIONS"}', None) is False


async def test_non_jwt_header_rejected() -> None:
    assert await verify_webhook(b"{}", "not-a-jwt") is False


async def test_wrong_algorithm_rejected() -> None:
    # A well-formed JWT but signed HS256 (not Plaid's ES256) must be refused
    # before any key lookup happens.
    token = jwt.encode({"request_body_sha256": "x"}, "secret", algorithm="HS256")
    assert await verify_webhook(b"{}", token) is False
