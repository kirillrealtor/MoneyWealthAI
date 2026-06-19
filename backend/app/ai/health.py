"""AI observability + graceful degradation (Architecture §17.3, §19.3).

Redis-backed so metrics and the degradation tier are shared across all app
replicas. Every helper FAILS OPEN — telemetry must never break a user request.

Degradation tiers (from the AI error rate over a 2-minute window):
  0 = healthy · 1 = degraded (elevated errors) · 2 = unhealthy (auto-fallback / shed)
"""
from __future__ import annotations

import time

from app.redis_client import redis_client

_CALLS = "aimetrics:calls"                 # hash: provider -> count
_ERRORS = "aimetrics:errors"               # hash: provider -> count
_TOKENS = "aimetrics:tokens"               # counter
_VALFAIL = "aimetrics:validation_failures"  # counter
_WIN = "aihealth:"                          # per-minute sliding window keys
_WIN_TTL = 300


async def record_ai_call(provider: str, ok: bool, tokens: int = 0) -> None:
    try:
        minute = int(time.time() // 60)
        pipe = redis_client.pipeline()
        pipe.hincrby(_CALLS, provider, 1)
        pipe.incr(f"{_WIN}calls:{minute}")
        pipe.expire(f"{_WIN}calls:{minute}", _WIN_TTL)
        if not ok:
            pipe.hincrby(_ERRORS, provider, 1)
            pipe.incr(f"{_WIN}errors:{minute}")
            pipe.expire(f"{_WIN}errors:{minute}", _WIN_TTL)
        if tokens:
            pipe.incrby(_TOKENS, tokens)
        await pipe.execute()
    except Exception:  # noqa: BLE001 - telemetry never breaks the request
        pass


async def record_validation_failure() -> None:
    try:
        await redis_client.incr(_VALFAIL)
    except Exception:  # noqa: BLE001
        pass


async def get_degradation_tier() -> int:
    try:
        now = int(time.time() // 60)
        calls = errors = 0
        for m in (now, now - 1):
            calls += int(await redis_client.get(f"{_WIN}calls:{m}") or 0)
            errors += int(await redis_client.get(f"{_WIN}errors:{m}") or 0)
        if calls < 5:
            return 0
        rate = errors / calls
        if rate > 0.20:
            return 2
        if rate > 0.05:
            return 1
        return 0
    except Exception:  # noqa: BLE001
        return 0


async def get_ai_stats() -> dict[str, object]:
    """Raw AI counters for the admin AI-ops surface. Fail-open to zeros."""
    try:
        calls = await redis_client.hgetall(_CALLS)  # type: ignore[misc]
        errors = await redis_client.hgetall(_ERRORS)  # type: ignore[misc]
        tokens = int(await redis_client.get(_TOKENS) or 0)
        valfail = int(await redis_client.get(_VALFAIL) or 0)
        tier = await get_degradation_tier()
    except Exception:  # noqa: BLE001
        calls, errors, tokens, valfail, tier = {}, {}, 0, 0, 0
    total_calls = sum(int(v) for v in calls.values())
    total_errors = sum(int(v) for v in errors.values())
    return {
        "tier": tier,
        "calls_total": total_calls,
        "errors_total": total_errors,
        "error_rate": round(total_errors / total_calls, 4) if total_calls else 0.0,
        "tokens_total": tokens,
        "validation_failures": valfail,
        "by_provider": {p: int(calls.get(p, 0)) for p in calls},
    }


async def prometheus_text() -> str:
    """Prometheus exposition for /metrics."""
    try:
        calls = await redis_client.hgetall(_CALLS)  # type: ignore[misc]
        errors = await redis_client.hgetall(_ERRORS)  # type: ignore[misc]
        tokens = int(await redis_client.get(_TOKENS) or 0)
        valfail = int(await redis_client.get(_VALFAIL) or 0)
        tier = await get_degradation_tier()
    except Exception:  # noqa: BLE001
        calls, errors, tokens, valfail, tier = {}, {}, 0, 0, 0

    lines = [
        "# HELP ai_calls_total Total AI provider calls.",
        "# TYPE ai_calls_total counter",
        *[f'ai_calls_total{{provider="{p}"}} {c}' for p, c in calls.items()],
        "# HELP ai_errors_total Failed AI provider calls.",
        "# TYPE ai_errors_total counter",
        *[f'ai_errors_total{{provider="{p}"}} {c}' for p, c in errors.items()],
        "# HELP ai_tokens_total Total tokens consumed.",
        "# TYPE ai_tokens_total counter",
        f"ai_tokens_total {tokens}",
        "# HELP ai_validation_failures_total Advisor outputs rejected by the validator.",
        "# TYPE ai_validation_failures_total counter",
        f"ai_validation_failures_total {valfail}",
        "# HELP ai_degradation_tier Current AI degradation tier (0 healthy..2 unhealthy).",
        "# TYPE ai_degradation_tier gauge",
        f"ai_degradation_tier {tier}",
    ]
    return "\n".join(lines) + "\n"
