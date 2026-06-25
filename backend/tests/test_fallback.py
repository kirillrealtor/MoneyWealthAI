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


def test_get_provider_auto_fallback_order(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.ai.provider import get_provider
    from app.config import settings

    monkeypatch.setattr(settings, "advisor_provider", "auto")
    monkeypatch.setattr(settings, "anthropic_api_key", "sk-claude")
    monkeypatch.setattr(settings, "gemini_api_key", "gemini-key")
    monkeypatch.setattr(settings, "grok_api_key", "grok-key")
    monkeypatch.setattr(settings, "groq_api_key", "groq-key")

    prov = get_provider()
    # It should return a FallbackProvider with the providers in order
    assert prov.name == "fallback"
    chain = prov._providers  # type: ignore[attr-defined]
    assert len(chain) == 4
    assert chain[0].name == "claude"
    assert chain[1].name == "gemini"
    assert chain[2].name == "grok"
    assert chain[3].name == "groq"


def test_get_provider_single_selected_and_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.ai.provider import get_provider
    from app.config import settings

    monkeypatch.setattr(settings, "advisor_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "gemini-key")
    monkeypatch.setattr(settings, "anthropic_api_key", "sk-claude")

    prov = get_provider()
    assert prov.name == "fallback"
    chain = prov._providers  # type: ignore[attr-defined]
    assert len(chain) == 1
    assert chain[0].name == "gemini"


def test_get_provider_raises_if_none_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.ai.provider import get_provider
    from app.config import settings
    from app.errors import ApiError

    monkeypatch.setattr(settings, "advisor_provider", "auto")
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    monkeypatch.setattr(settings, "gemini_api_key", None)
    monkeypatch.setattr(settings, "grok_api_key", None)
    monkeypatch.setattr(settings, "groq_api_key", None)

    with pytest.raises(ApiError) as exc_info:
        get_provider()
    assert exc_info.value.code == "AI_UNAVAILABLE"
