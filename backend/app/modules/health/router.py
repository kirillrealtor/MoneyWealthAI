"""Liveness + readiness probes.

/health is shallow (process up). /health/ready checks that Aurora and Redis are
reachable - used by the load balancer / ECS.
"""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse

from app import db
from app.ai.health import get_degradation_tier, prometheus_text
from app.redis_client import redis_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "ts": datetime.now(UTC).isoformat()}


@router.get("/health/ready")
async def ready() -> JSONResponse:
    checks = {"db": "fail", "redis": "fail"}
    try:
        await db.fetchval("SELECT 1")
        checks["db"] = "ok"
    except Exception:  # noqa: BLE001
        pass
    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception:  # noqa: BLE001
        pass
    healthy = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ready" if healthy else "degraded", "checks": checks},
    )


@router.get("/health/ai")
async def ai_health() -> dict[str, int | str]:
    """AI degradation tier (0 healthy, 1 degraded, 2 unhealthy)."""
    tier = await get_degradation_tier()
    return {"tier": tier, "status": ("healthy", "degraded", "unhealthy")[tier]}


@router.get("/metrics")
async def metrics() -> PlainTextResponse:
    """Prometheus exposition. Network-internal in production (scraped, not public)."""
    return PlainTextResponse(await prometheus_text(), media_type="text/plain; version=0.0.4")
