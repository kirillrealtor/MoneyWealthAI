"""LLM provider abstraction + Claude implementation of the agentic tool loop.

Behind one `AdvisorProvider` interface so a GPT-4o/Gemini fallback can be added
later (Architecture §17.4) without touching callers. The loop holds NO database
connection while Claude is thinking — tool executors open their own short
tenant-scoped transactions.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, cast

import anthropic

from app.config import settings
from app.errors import ApiError
from app.logging_conf import logger

# Callback the advisor passes in; executes one tool and returns (content, is_error).
# It binds user_id/tenant_id server-side — the model never supplies them.
ToolExecutor = Callable[[str, dict[str, Any]], Awaitable[tuple[str, bool]]]


@dataclass
class AdvisorResult:
    text: str
    provider: str
    model: str
    tool_calls_made: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class AdvisorProvider(Protocol):
    name: str

    async def run(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        execute_tool: ToolExecutor,
    ) -> AdvisorResult: ...


class ClaudeProvider:
    name = "claude"

    def __init__(self) -> None:
        if not settings.anthropic_configured:
            raise ApiError("AI_UNAVAILABLE")
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.advisor_model

    async def run(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        execute_tool: ToolExecutor,
    ) -> AdvisorResult:
        convo = list(messages)
        tool_calls: list[str] = []
        in_tok = out_tok = 0

        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": settings.advisor_max_tokens,
            "system": system,
            "tools": tools,
        }
        if settings.advisor_thinking:
            kwargs["thinking"] = {"type": "adaptive"}

        for _round in range(settings.advisor_max_tool_rounds + 1):
            # SDK accepts dict message params at runtime (TypedDict); annotate-only mismatch.
            resp = await self._client.messages.create(messages=convo, **kwargs)  # type: ignore[arg-type]
            in_tok += resp.usage.input_tokens
            out_tok += resp.usage.output_tokens

            if resp.stop_reason != "tool_use":
                text = next((b.text for b in resp.content if b.type == "text"), "")
                return AdvisorResult(
                    text=text, provider=self.name, model=self._model,
                    tool_calls_made=tool_calls, input_tokens=in_tok, output_tokens=out_tok,
                )

            # Execute every requested tool, append assistant turn + tool results.
            convo.append({"role": "assistant", "content": resp.content})
            results: list[dict[str, Any]] = []
            for block in resp.content:
                if block.type == "tool_use":
                    tool_calls.append(block.name)
                    content, is_error = await execute_tool(block.name, cast("dict[str, Any]", block.input))
                    results.append({
                        "type": "tool_result", "tool_use_id": block.id,
                        "content": content, "is_error": is_error,
                    })
            convo.append({"role": "user", "content": results})

        # Exhausted tool rounds without a final answer — return what we have.
        logger.warning("advisor tool rounds exhausted", service="ai-advisor", tool_calls=tool_calls)
        return AdvisorResult(
            text="I wasn't able to complete that analysis. Could you rephrase or narrow the question?",
            provider=self.name, model=self._model, tool_calls_made=tool_calls,
            input_tokens=in_tok, output_tokens=out_tok,
        )


class FallbackProvider:
    """Tries providers in order, failing over on error (Architecture §17.4 — Tier
    2 degradation). Records each attempt for the AI health/degradation metrics."""

    name = "fallback"

    def __init__(self, providers: list[AdvisorProvider]) -> None:
        self._providers = providers

    async def run(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        execute_tool: ToolExecutor,
    ) -> AdvisorResult:
        from .health import record_ai_call

        last_err: Exception | None = None
        for i, prov in enumerate(self._providers):
            try:
                result = await prov.run(system=system, messages=messages, tools=tools, execute_tool=execute_tool)
                await record_ai_call(prov.name, ok=True, tokens=result.total_tokens)
                return result
            except Exception as err:  # noqa: BLE001 - try the next provider
                last_err = err
                await record_ai_call(prov.name, ok=False)
                logger.warning("ai provider failed; failing over", service="ai-advisor",
                               provider=prov.name, remaining=len(self._providers) - i - 1, error_message=str(err))
        if last_err is not None:
            raise last_err
        raise ApiError("AI_UNAVAILABLE")


def get_provider() -> AdvisorProvider:
    """Build the provider chain (with auto-fallback), or a clean 503 if none is
    configured. 'auto' prefers Claude, then Gemini, then Grok, and falls back to Groq."""
    def _groq() -> AdvisorProvider:
        from .groq_provider import GroqProvider
        return GroqProvider()

    def _gemini() -> AdvisorProvider:
        from .gemini_provider import GeminiProvider
        return GeminiProvider()

    def _grok() -> AdvisorProvider:
        from .grok_provider import GrokProvider
        return GrokProvider()

    def _mock() -> AdvisorProvider:
        from .mock_provider import MockProvider
        return MockProvider()  # type: ignore[return-value]

    choice = settings.advisor_provider
    providers: list[AdvisorProvider] = []
    if choice == "claude":
        if settings.anthropic_configured:
            providers = [ClaudeProvider()]
    elif choice == "gemini":
        if settings.gemini_configured:
            providers = [_gemini()]
    elif choice == "grok":
        if settings.grok_configured:
            providers = [_grok()]
    elif choice == "groq":
        if settings.groq_configured:
            providers = [_groq()]
    elif choice == "mock":
        providers = [_mock()]
    else:  # auto — prefer Claude, then Gemini, then Grok, then Groq
        if settings.anthropic_configured:
            providers.append(ClaudeProvider())
        if settings.gemini_configured:
            providers.append(_gemini())
        if settings.grok_configured:
            providers.append(_grok())
        if settings.groq_configured:
            providers.append(_groq())
        
        # local mock fallback in development when no external AI keys are configured
        if not providers and settings.env == "development":
            providers.append(_mock())

    if not providers:
        raise ApiError("AI_UNAVAILABLE")
    return FallbackProvider(providers)
