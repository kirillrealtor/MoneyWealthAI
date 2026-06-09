"""Eval framework tests — assertion checkers + the runner (scripted provider,
no live LLM)."""
from __future__ import annotations

from app.ai.provider import AdvisorResult
from app.evals.assertions import evaluate
from app.evals.golden_set import EvalCase
from app.evals.runner import run_case


def test_assertion_checkers() -> None:
    assert evaluate(("tool_called", "get_x"), "", ["get_x"])[0] is True
    assert evaluate(("tool_called", "get_x"), "", [])[0] is False
    assert evaluate(("no_directive",), "You should buy AAPL today", [])[0] is False
    assert evaluate(("no_directive",), "Consider your options carefully", [])[0] is True
    assert evaluate(("compliance",), "This is educational, not financial advice.", [])[0] is True
    assert evaluate(("compliance",), "Just buy it.", [])[0] is False
    assert evaluate(("grounded",), "You have $100.", [])[0] is False
    assert evaluate(("grounded",), "You have $100.", ["get_account_balances"])[0] is True
    assert evaluate(("grounded",), "No numbers here.", [])[0] is True
    assert evaluate(("max_words", "3"), "a b c d", [])[0] is False


class _ScriptedProvider:
    name = "scripted"

    def __init__(self, text: str, tool: str | None = None) -> None:
        self._text, self._tool = text, tool

    async def run(self, *, system, messages, tools, execute_tool):  # type: ignore[no-untyped-def]
        made: list[str] = []
        if self._tool:
            await execute_tool(self._tool, {})
            made.append(self._tool)
        return AdvisorResult(text=self._text, provider="scripted", model="x",
                             tool_calls_made=made, input_tokens=10, output_tokens=5)


async def test_runner_scores_good_case() -> None:
    case = EvalCase(
        id="T1", description="", user_message="spend?", persona="balanced",
        assertions=[("tool_called", "get_spending_summary"), ("grounded",)],
    )
    provider = _ScriptedProvider("You spent $487.32 recently. Next, set a budget.", tool="get_spending_summary")
    result = await run_case(provider, case)  # type: ignore[arg-type]
    assert result.passed is True
    assert result.failures == []


async def test_runner_catches_ungrounded_number() -> None:
    case = EvalCase(id="T2", description="", user_message="spend?", persona="balanced", assertions=[("grounded",)])
    provider = _ScriptedProvider("You spent $999 recently.")  # number, no tool call
    result = await run_case(provider, case)  # type: ignore[arg-type]
    assert result.passed is False
    assert any("grounded" in f for f in result.failures)
