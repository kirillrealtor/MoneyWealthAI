"""Eval runner: replays each golden case through a provider with MOCKED tools
(no DB, no persistence) and scores the rule-based assertions."""
from __future__ import annotations

import json
from dataclasses import dataclass

from app.ai.prompts import build_system_prompt
from app.ai.provider import AdvisorProvider
from app.ai.snapshot import FinancialSnapshot
from app.ai.tools import TOOL_DEFINITIONS

from .assertions import evaluate
from .golden_set import GOLDEN_SET, EvalCase

# Fixed snapshot so the system prompt is deterministic across runs.
_MOCK_SNAPSHOT = FinancialSnapshot(
    net_worth=12000.0, total_debt=3000.0, monthly_income=5500.0,
    monthly_spend=4200.0, savings_rate=23.0, has_linked_accounts=True,
)


@dataclass
class CaseResult:
    case_id: str
    passed: bool
    failures: list[str]
    tool_calls: list[str]
    tokens: int


async def run_case(provider: AdvisorProvider, case: EvalCase) -> CaseResult:
    system = build_system_prompt(first_name="Alex", persona=case.persona, snapshot=_MOCK_SNAPSHOT)

    async def execute_tool(name: str, _raw: dict[str, object]) -> tuple[str, bool]:
        return json.dumps(case.mock_tool_results.get(name, {"note": "no data"}), default=str), False

    result = await provider.run(
        system=system, messages=[{"role": "user", "content": case.user_message}],
        tools=TOOL_DEFINITIONS, execute_tool=execute_tool,
    )
    failures = [detail for spec in case.assertions
                for ok, detail in [evaluate(spec, result.text, result.tool_calls_made)] if not ok]
    return CaseResult(case.id, not failures, failures, result.tool_calls_made, result.total_tokens)


async def run_all(provider: AdvisorProvider, cases: list[EvalCase] | None = None) -> tuple[float, list[CaseResult]]:
    cases = cases if cases is not None else GOLDEN_SET
    results = [await run_case(provider, c) for c in cases]
    pass_rate = (sum(r.passed for r in results) / len(results) * 100) if results else 0.0
    return pass_rate, results
