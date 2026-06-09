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


def get_provider() -> AdvisorProvider:
    """Select the configured provider, or a clean 503 if none is configured.
    'auto' prefers Claude (quality for financial reasoning) and falls back to
    Groq if only Groq is set."""
    choice = settings.advisor_provider
    if choice == "groq" or (choice == "auto" and settings.groq_configured and not settings.anthropic_configured):
        from .groq_provider import GroqProvider
        return GroqProvider()
    if choice == "claude" or settings.anthropic_configured:
        return ClaudeProvider()
    if settings.groq_configured:
        from .groq_provider import GroqProvider
        return GroqProvider()
    raise ApiError("AI_UNAVAILABLE")
