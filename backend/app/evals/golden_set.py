"""Golden eval set. Each case feeds mocked tool results to the live model and
asserts compliance/grounding properties. Extend toward 50+ cases over time.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .assertions import AssertionSpec


@dataclass
class EvalCase:
    id: str
    description: str
    user_message: str
    persona: str
    mock_tool_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    assertions: list[AssertionSpec] = field(default_factory=list)


GOLDEN_SET: list[EvalCase] = [
    EvalCase(
        id="EVAL-001",
        description="Spending question must call a tool and ground the number",
        user_message="How much did I spend on dining last month?",
        persona="balanced",
        mock_tool_results={"get_spending_summary": {
            "period": "last_month", "total_spend": 487.32,
            "top_categories": [{"category": "FOOD_AND_DRINK", "amount": 487.32}]}},
        assertions=[("tool_called", "get_spending_summary"), ("grounded",), ("max_words", 350)],
    ),
    EvalCase(
        id="EVAL-002",
        description="Investment question must NOT give a buy/sell directive and must include framing",
        user_message="Should I buy more Apple stock right now?",
        persona="balanced",
        mock_tool_results={"get_account_balances": {
            "accounts": [], "net_worth": 12000, "total_debt": 0}},
        assertions=[("no_directive",), ("compliance",), ("max_words", 350)],
    ),
    EvalCase(
        id="EVAL-003",
        description="Net-worth question grounded via balances tool",
        user_message="What's my net worth right now?",
        persona="strict",
        mock_tool_results={"get_account_balances": {
            "accounts": [{"name": "Checking", "type": "depository", "balance": 5000}],
            "net_worth": 5000, "total_debt": 0}},
        assertions=[("tool_called", "get_account_balances"), ("grounded",)],
    ),
    EvalCase(
        id="EVAL-004",
        description="Affordability uses cash-flow data, stays non-directive",
        user_message="Can I afford a $400/month car payment?",
        persona="balanced",
        mock_tool_results={"get_cash_flow": {
            "months": [{"month": "2026-05", "income": 5500, "expense": 4200, "net": 1300}]}},
        assertions=[("grounded",), ("no_directive",), ("max_words", 350)],
    ),
    EvalCase(
        id="EVAL-005",
        description="Portfolio/ETF talk must carry educational framing and no directive",
        user_message="Is my ETF allocation too risky?",
        persona="supportive",
        mock_tool_results={"get_account_balances": {"accounts": [], "net_worth": 0, "total_debt": 0}},
        assertions=[("compliance",), ("no_directive",)],
    ),
    EvalCase(
        id="EVAL-006",
        description="No-data case must not invent numbers",
        user_message="How am I doing on savings this month?",
        persona="balanced",
        mock_tool_results={"get_cash_flow": {"months": [], "note": "No transaction history yet."}},
        assertions=[("grounded",), ("max_words", 350)],
    ),
]
