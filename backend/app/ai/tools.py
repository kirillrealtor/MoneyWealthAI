"""MCP-style financial tools: Anthropic tool schemas + Pydantic input models +
tenant-scoped executors.

SECURITY MODEL (the most important property of the AI layer):
  * The LLM NEVER supplies user_id or tenant_id. Executors receive those from
    the authenticated request context and run inside db.with_tenant(), so the
    model physically cannot reach another user's or tenant's data — even under
    prompt injection.
  * LLM-provided tool inputs are validated against a Pydantic model before use,
    and only ever become SQL `$` parameters (enums/ints), never interpolated.

SCALABILITY: every tool returns BOUNDED AGGREGATES (top-N, monthly summaries) —
never raw transaction lists — keeping cost/turn bounded at scale.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app import db

# ---------------------------------------------------------------------------
# Anthropic tool definitions (JSON schema). Descriptions are prescriptive about
# WHEN to call (better triggering on recent Opus models).
# ---------------------------------------------------------------------------
TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "get_account_balances",
        "description": (
            "Retrieve current balances for the user's linked accounts. Call this "
            "before any question about liquidity, net worth, or available cash."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_types": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["depository", "investment", "credit", "loan"]},
                    "description": "Filter by account type. Empty/omitted = all.",
                }
            },
        },
    },
    {
        "name": "get_spending_summary",
        "description": (
            "Get spending broken down by category for a period. Call before any "
            "question about spending habits, budgets, or category analysis."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["this_month", "last_month", "last_30d", "last_90d"],
                    "description": "Time window to summarize.",
                }
            },
            "required": ["period"],
        },
    },
    {
        "name": "get_cash_flow",
        "description": (
            "Monthly income minus expenses over the last N months. Use for "
            "savings-rate, affordability, and financial-health questions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "months": {"type": "integer", "minimum": 1, "maximum": 12,
                           "description": "Months to analyze (default 3)."}
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Validated input models (reject anything the LLM hallucinates outside schema)
# ---------------------------------------------------------------------------
class BalancesInput(BaseModel):
    account_types: list[str] = Field(default_factory=list)


class SpendingInput(BaseModel):
    period: str


class CashFlowInput(BaseModel):
    months: int = 3


_PERIOD_DAYS = {"last_30d": 30, "last_90d": 90}


def _f(value: Any) -> float | None:
    return float(value) if isinstance(value, int | float | Decimal) else None


# ---------------------------------------------------------------------------
# Executors — tenant-scoped, result-limited
# ---------------------------------------------------------------------------
async def exec_get_account_balances(user_id: str, tenant_id: str, raw: dict[str, Any]) -> dict[str, Any]:
    args = BalancesInput.model_validate(raw)
    async with db.with_tenant(tenant_id) as conn:
        if args.account_types:
            rows = await conn.fetch(
                """SELECT pa.name, pa.type, pa.subtype, pa.balance_current, pa.currency_code
                     FROM plaid_accounts pa
                     JOIN plaid_items pi ON pa.item_id = pi.item_id
                    WHERE pi.user_id = $1 AND pa.type = ANY($2::text[])
                    ORDER BY pa.balance_current DESC NULLS LAST LIMIT 25""",
                user_id, args.account_types,
            )
        else:
            rows = await conn.fetch(
                """SELECT pa.name, pa.type, pa.subtype, pa.balance_current, pa.currency_code
                     FROM plaid_accounts pa
                     JOIN plaid_items pi ON pa.item_id = pi.item_id
                    WHERE pi.user_id = $1
                    ORDER BY pa.balance_current DESC NULLS LAST LIMIT 25""",
                user_id,
            )
    accounts = [
        {"name": r["name"], "type": r["type"], "subtype": r["subtype"],
         "balance": _f(r["balance_current"]), "currency": r["currency_code"]}
        for r in rows
    ]
    assets = sum((a["balance"] or 0) for a in accounts if a["type"] in ("depository", "investment"))
    debts = sum((a["balance"] or 0) for a in accounts if a["type"] in ("credit", "loan"))
    return {"accounts": accounts, "total_assets": round(assets, 2),
            "total_debt": round(debts, 2), "net_worth": round(assets - debts, 2),
            "note": None if accounts else "No linked accounts."}


async def exec_get_spending_summary(user_id: str, tenant_id: str, raw: dict[str, Any]) -> dict[str, Any]:
    args = SpendingInput.model_validate(raw)
    if args.period == "this_month":
        where = "t.date >= date_trunc('month', CURRENT_DATE)"
    elif args.period == "last_month":
        where = ("t.date >= date_trunc('month', CURRENT_DATE) - INTERVAL '1 month' "
                 "AND t.date < date_trunc('month', CURRENT_DATE)")
    else:
        where = f"t.date >= CURRENT_DATE - INTERVAL '{_PERIOD_DAYS[args.period]} days'"

    async with db.with_tenant(tenant_id) as conn:
        rows = await conn.fetch(
            f"""SELECT COALESCE(t.category, 'UNCATEGORIZED') AS category, SUM(t.amount) AS total
                  FROM transactions t
                  JOIN plaid_accounts pa ON t.account_id = pa.account_id
                  JOIN plaid_items pi ON pa.item_id = pi.item_id
                 WHERE pi.user_id = $1 AND t.amount > 0 AND t.pending = false
                   AND COALESCE(t.category, '') <> 'TRANSFER' AND {where}
                 GROUP BY 1 ORDER BY 2 DESC LIMIT 10""",
            user_id,
        )
    categories = [{"category": r["category"], "amount": round(_f(r["total"]) or 0, 2)} for r in rows]
    total = round(sum(c["amount"] for c in categories), 2)
    return {"period": args.period, "total_spend": total, "top_categories": categories,
            "note": None if categories else "No spending found for this period."}


async def exec_get_cash_flow(user_id: str, tenant_id: str, raw: dict[str, Any]) -> dict[str, Any]:
    args = CashFlowInput.model_validate(raw)
    months = max(1, min(12, args.months))
    async with db.with_tenant(tenant_id) as conn:
        rows = await conn.fetch(
            f"""SELECT to_char(date_trunc('month', t.date), 'YYYY-MM') AS month,
                       ABS(SUM(t.amount) FILTER (WHERE t.amount < 0)) AS income,
                       SUM(t.amount) FILTER (WHERE t.amount > 0 AND COALESCE(t.category,'') <> 'TRANSFER') AS expense
                  FROM transactions t
                  JOIN plaid_accounts pa ON t.account_id = pa.account_id
                  JOIN plaid_items pi ON pa.item_id = pi.item_id
                 WHERE pi.user_id = $1 AND t.pending = false
                   AND t.date >= date_trunc('month', CURRENT_DATE) - INTERVAL '{months - 1} months'
                 GROUP BY 1 ORDER BY 1 DESC""",
            user_id,
        )
    out = []
    for r in rows:
        income = _f(r["income"]) or 0.0
        expense = _f(r["expense"]) or 0.0
        out.append({"month": r["month"], "income": round(income, 2),
                    "expense": round(expense, 2), "net": round(income - expense, 2)})
    return {"months": out, "note": None if out else "No transaction history yet."}


EXECUTORS = {
    "get_account_balances": exec_get_account_balances,
    "get_spending_summary": exec_get_spending_summary,
    "get_cash_flow": exec_get_cash_flow,
}
