"""Integration fixtures. Skip the whole module if Postgres isn't reachable so
unit-only runs (no datastores) stay green."""
from __future__ import annotations

import socket
from collections.abc import AsyncIterator

import httpx
import pytest
from httpx import ASGITransport


def _db_reachable() -> bool:
    return True


pytestmark = pytest.mark.skipif(not _db_reachable(), reason="SQLite is always reachable")


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    # Import here so the skip above applies before any DB wiring.
    from app import db
    from app.main import app

    await db.init_pool()
    try:
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
            yield c
    finally:
        await db.close_pool()
