"""Provider auto-fallback (Tier-2 degradation) — unit, no LLM/datastore."""
from __future__ import annotations

from typing import Any

import pytest

from app.ai.provider import AdvisorResult, FallbackProvider


async def _noop_tool(_name: str, _raw: dict[str, Any]) -> tuple[str, bool]:
    return "{}", False


class _Boom:
    name = "boom"

    async def run(self, **_kw: Any) -> AdvisorResult:
        raise RuntimeError("provider down")


class _Ok:
    name = "ok"

    async def run(self, **_kw: Any) -> AdvisorResult:
        return AdvisorResult(text="ok", provider="ok", model="m", tool_calls_made=[],
                             input_tokens=1, output_tokens=1)


async def test_fallback_skips_failed_provider() -> None:
    fp = FallbackProvider([_Boom(), _Ok()])  # type: ignore[list-item]
    res = await fp.run(system="", messages=[], tools=[], execute_tool=_noop_tool)
    assert res.provider == "ok"


async def test_fallback_raises_when_all_providers_fail() -> None:
    fp = FallbackProvider([_Boom(), _Boom()])  # type: ignore[list-item]
    with pytest.raises(RuntimeError):
        await fp.run(system="", messages=[], tools=[], execute_tool=_noop_tool)
