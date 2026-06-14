"""Budget business logic — tenant-scoped (RLS) with app-layer user checks."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

import asyncpg

from app import db
from app.errors import ApiError


async def create_budget(
    user_id: str, tenant_id: str, *, category: str, monthly_limit: Decimal, alert_at_pct: int
) -> str:
    async with db.with_tenant(tenant_id, user_id) as conn:
        exists = await conn.fetchval(
            "SELECT 1 FROM budgets WHERE user_id = $1 AND category = $2", user_id, category
        )
        if exists:
            raise ApiError("CONFLICT", message="A budget for this category already exists.")
        try:
            return str(await conn.fetchval(
                """INSERT INTO budgets (user_id, tenant_id, category, monthly_limit, alert_at_pct)
                   VALUES ($1, $2, $3, $4, $5) RETURNING budget_id""",
                user_id, tenant_id, category, monthly_limit, alert_at_pct,
            ))
        except asyncpg.UniqueViolationError as err:  # concurrent create of the same category
            raise ApiError("CONFLICT", message="A budget for this category already exists.") from err


async def list_status(user_id: str, tenant_id: str) -> list[dict[str, Any]]:
    async with db.with_tenant(tenant_id, user_id) as conn:
        budgets = await conn.fetch(
            """SELECT budget_id, category, monthly_limit, alert_at_pct, is_active
                 FROM budgets WHERE user_id = $1 ORDER BY category""",
            user_id,
        )
        spend = await conn.fetch(
            """SELECT t.category AS category, SUM(t.amount) AS spent
                 FROM transactions t
                 JOIN plaid_accounts pa ON t.account_id = pa.account_id
                 JOIN plaid_items pi ON pa.item_id = pi.item_id
                WHERE pi.user_id = $1 AND t.amount > 0 AND t.pending = false
                  AND COALESCE(t.category, '') <> ALL(ARRAY['TRANSFER','TRANSFER_IN','TRANSFER_OUT','LOAN_PAYMENTS'])
                  AND t.date >= date_trunc('month', CURRENT_DATE)
                GROUP BY 1""",
            user_id,
        )
    spent_by_cat = {r["category"]: r["spent"] for r in spend}
    result: list[dict[str, Any]] = []
    for b in budgets:
        spent_val = spent_by_cat.get(b["category"]) or Decimal("0")
        limit = b["monthly_limit"]
        pct = float(spent_val / limit * 100) if limit > 0 else 0.0
        result.append({
            "budget_id": str(b["budget_id"]), "category": b["category"],
            "monthly_limit": limit, "spent": spent_val.quantize(Decimal("0.01")),
            "pct_used": round(pct, 1), "remaining": (limit - spent_val).quantize(Decimal("0.01")),
            "alert_at_pct": b["alert_at_pct"], "is_active": b["is_active"],
        })
    return result


async def update_budget(
    user_id: str, tenant_id: str, budget_id: str,
    *, monthly_limit: Decimal | None, alert_at_pct: int | None, is_active: bool | None,
) -> None:
    async with db.with_tenant(tenant_id, user_id) as conn:
        status = await conn.execute(
            """UPDATE budgets SET
                   monthly_limit = COALESCE($3, monthly_limit),
                   alert_at_pct  = COALESCE($4, alert_at_pct),
                   is_active     = COALESCE($5, is_active)
                WHERE budget_id = $1 AND user_id = $2""",
            budget_id, user_id, monthly_limit, alert_at_pct, is_active,
        )
    if status.split()[-1] == "0":  # "UPDATE 0" / "DELETE 0" -> no row matched
        raise ApiError("NOT_FOUND")


async def delete_budget(user_id: str, tenant_id: str, budget_id: str) -> None:
    async with db.with_tenant(tenant_id, user_id) as conn:
        status = await conn.execute(
            "DELETE FROM budgets WHERE budget_id = $1 AND user_id = $2", budget_id, user_id
        )
    if status.split()[-1] == "0":  # "UPDATE 0" / "DELETE 0" -> no row matched
        raise ApiError("NOT_FOUND")
