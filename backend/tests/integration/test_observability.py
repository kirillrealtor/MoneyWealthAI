"""AI metrics + degradation endpoints (needs Redis, co-located with Postgres)."""
from __future__ import annotations

import httpx
import pytest

from app.ai.health import get_degradation_tier, prometheus_text, record_ai_call
from tests.integration.conftest import _db_reachable

pytestmark = pytest.mark.skipif(not _db_reachable(), reason="datastores not reachable")


async def test_metrics_record_and_expose(client: httpx.AsyncClient) -> None:
    await record_ai_call("claude", ok=True, tokens=100)
    await record_ai_call("claude", ok=False)
    text = await prometheus_text()
    assert "ai_calls_total" in text
    assert "ai_tokens_total" in text
    assert "ai_degradation_tier" in text


async def test_metrics_and_ai_health_endpoints(client: httpx.AsyncClient) -> None:
    r = await client.get("/metrics")
    assert r.status_code == 200
    assert "ai_degradation_tier" in r.text

    h = await client.get("/health/ai")
    assert h.status_code == 200
    body = h.json()
    assert body["tier"] in (0, 1, 2)
    assert isinstance(await get_degradation_tier(), int)
