"""Debt dashboard logic — tenant-scoped reads over Plaid-synced debt_accounts,
analysis via the exact calculation engine. Read-only; no directives.

NOTE: debt_accounts is populated by the Plaid liabilities sync (deferred to the
Phase 2 follow-up). When that sync is built, APR MUST be normalized to a decimal
fraction (0.2499), not a percentage (24.99) — a unit mismatch makes every
interest/payoff number 100x wrong. See docs/PHASE2_PENDING.md.
"""
from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any

from app import db
from app.calculations.debt import Debt, calculate_debt_payoff, debt_to_income, months_at_minimum

# APR above which a debt of this type is flagged "above typical" (refinance worth
# investigating). Neutral signal, not advice.
_TYPICAL_APR = {
    "credit_card": Decimal("0.20"), "personal": Decimal("0.15"),
    "auto": Decimal("0.10"), "student_loan": Decimal("0.08"),
}
_EXCL_TRANSFERS = "COALESCE(t.category, '') <> ALL(ARRAY['TRANSFER','TRANSFER_IN','TRANSFER_OUT','LOAN_PAYMENTS'])"
_MAX_DEBTS = 200  # bound the result set (memory / DoS guard at scale)


async def _fetch_rows(conn: Any, user_id: str) -> list[Any]:
    return list(await conn.fetch(
        f"""SELECT da.debt_id, da.debt_type, da.balance, da.apr, da.minimum_payment
              FROM debt_accounts da
              JOIN plaid_accounts pa ON da.account_id = pa.account_id
              JOIN plaid_items pi ON pa.item_id = pi.item_id
             WHERE pi.user_id = $1 ORDER BY da.apr DESC NULLS LAST LIMIT {_MAX_DEBTS}""",
        user_id,
    ))


async def _avg_monthly_income(conn: Any, user_id: str) -> Decimal:
    # Average over the months that actually have income, not a hardcoded 3 — so a
    # user with <3 months of data isn't shown an understated income / inflated DTI.
    rows = await conn.fetch(
        f"""SELECT ABS(SUM(t.amount) FILTER (WHERE t.amount < 0 AND {_EXCL_TRANSFERS})) AS income
              FROM transactions t
              JOIN plaid_accounts pa ON t.account_id = pa.account_id
              JOIN plaid_items pi ON pa.item_id = pi.item_id
             WHERE pi.user_id = $1 AND t.pending = false
               AND t.date >= date_trunc('month', CURRENT_DATE) - INTERVAL '2 months'
             GROUP BY date_trunc('month', t.date)""",
        user_id,
    )
    incomes = [Decimal(r["income"]) for r in rows if r["income"] and r["income"] > 0]
    return (sum(incomes, Decimal("0")) / Decimal(len(incomes))) if incomes else Decimal("0")


def _summarize(rows: list[Any], income: Decimal) -> dict[str, Any]:
    """Pure CPU (runs in a thread so the per-debt amortization loops never block
    the event loop)."""
    debts: list[dict[str, Any]] = []
    total_debt = Decimal("0")
    total_min = Decimal("0")
    for r in rows:
        balance = r["balance"] or Decimal("0")
        apr = r["apr"] or Decimal("0")
        minimum = r["minimum_payment"] or Decimal("0")
        total_debt += balance
        total_min += minimum
        threshold = _TYPICAL_APR.get(r["debt_type"] or "", Decimal("0.18"))
        debts.append({
            "debt_id": str(r["debt_id"]), "debt_type": r["debt_type"], "balance": r["balance"],
            "apr": r["apr"], "minimum_payment": r["minimum_payment"],
            "months_at_minimum": months_at_minimum(balance, apr, minimum),
            "above_typical_rate": apr > threshold,
        })
    dti = debt_to_income(total_min, income)
    return {
        "debts": debts, "total_debt": total_debt.quantize(Decimal("0.01")),
        "total_minimum_payment": total_min.quantize(Decimal("0.01")),
        "debt_to_income": float(dti) if dti is not None else None,
        "note": None if debts else "No debt accounts linked.",
    }


async def get_summary(user_id: str, tenant_id: str) -> dict[str, Any]:
    async with db.with_tenant(tenant_id) as conn:
        rows = await _fetch_rows(conn, user_id)
        income = await _avg_monthly_income(conn, user_id)
    return await asyncio.to_thread(_summarize, rows, income)


async def payoff_comparison(user_id: str, tenant_id: str, extra: Decimal) -> dict[str, Any]:
    async with db.with_tenant(tenant_id) as conn:
        rows = await _fetch_rows(conn, user_id)
    objs = [Debt(id=str(r["debt_id"]), balance=r["balance"] or Decimal("0"),
                 apr=r["apr"] or Decimal("0"), minimum_payment=r["minimum_payment"] or Decimal("0"))
            for r in rows if (r["balance"] or Decimal("0")) > 0]
    if not objs:
        empty = {"payoff_order": [], "months_to_payoff": 0, "total_interest": Decimal("0.00"), "feasible": True}
        return {"avalanche": empty, "snowball": empty,
                "interest_saved_with_avalanche": Decimal("0.00"), "note": "No debt accounts linked."}
    # Heavy month-by-month simulation runs off the event loop.
    plans = await asyncio.to_thread(calculate_debt_payoff, objs, extra)
    av, sn = plans["avalanche"], plans["snowball"]
    return {
        "avalanche": {"payoff_order": av.payoff_order, "months_to_payoff": av.months_to_payoff,
                      "total_interest": av.total_interest, "feasible": av.feasible},
        "snowball": {"payoff_order": sn.payoff_order, "months_to_payoff": sn.months_to_payoff,
                     "total_interest": sn.total_interest, "feasible": sn.feasible},
        "interest_saved_with_avalanche": (sn.total_interest - av.total_interest).quantize(Decimal("0.01")),
        "note": None,
    }
