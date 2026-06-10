from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app import db
from app.audit import audit
from app.errors import ApiError
from app.logging_conf import logger

from .schemas import PLAID_CATEGORIES, BudgetResponse, DebtAccountResponse, DebtSummaryResponse, HoldingResponse, PortfolioSummaryResponse


async def create_budget(user_id: str, tenant_id: str, category: PLAID_CATEGORIES, monthly_limit: Decimal, alert_at_pct: int) -> str:
    async with db.with_tenant(tenant_id) as conn:
        budget_id = await conn.fetchval(
            """INSERT INTO budgets (user_id, tenant_id, category, monthly_limit, alert_at_pct)
               VALUES ($1, $2, $3, $4, $5) RETURNING budget_id""",
            user_id, tenant_id, category, monthly_limit, alert_at_pct,
        )
    await audit("planning.budget_created", user_id=user_id, tenant_id=tenant_id, resource="budget", resource_id=budget_id)
    return budget_id


async def get_budgets(user_id: str, tenant_id: str) -> list[BudgetResponse]:
    async with db.with_tenant(tenant_id) as conn:
        budgets = await conn.fetch(
            "SELECT budget_id, category, monthly_limit, alert_at_pct, created_at FROM budgets WHERE user_id = $1 ORDER BY created_at DESC",
            user_id,
        )
    
    result = []
    for b in budgets:
        spent = await calculate_budget_spent(user_id, tenant_id, b["category"])
        result.append(BudgetResponse(
            budget_id=str(b["budget_id"]),
            category=b["category"],
            monthly_limit=b["monthly_limit"],
            spent_this_month=spent,
            alert_at_pct=b["alert_at_pct"],
            created_at=b["created_at"].isoformat(),
        ))
    return result


async def calculate_budget_spent(user_id: str, tenant_id: str, category: str) -> Decimal:
    async with db.with_tenant(tenant_id) as conn:
        result = await conn.fetchval(
            """SELECT COALESCE(SUM(t.amount), 0)
               FROM transactions t
               JOIN plaid_accounts pa ON t.account_id = pa.account_id
               JOIN plaid_items pi ON pa.item_id = pi.item_id
               WHERE pi.user_id = $1 AND t.category = $2 AND t.date >= DATE_TRUNC('month', NOW())""",
            user_id, category,
        )
    return Decimal(str(result)) if result else Decimal(0)


async def update_budget(user_id: str, tenant_id: str, budget_id: str, monthly_limit: Decimal) -> bool:
    async with db.with_tenant(tenant_id) as conn:
        result = await conn.execute(
            "UPDATE budgets SET monthly_limit = $1 WHERE budget_id = $2 AND user_id = $3",
            monthly_limit, budget_id, user_id,
        )
    if result == "UPDATE 0":
        raise ApiError("NOT_FOUND")
    await audit("planning.budget_updated", user_id=user_id, tenant_id=tenant_id, resource="budget", resource_id=budget_id)
    return True


async def delete_budget(user_id: str, tenant_id: str, budget_id: str) -> bool:
    async with db.with_tenant(tenant_id) as conn:
        result = await conn.execute(
            "DELETE FROM budgets WHERE budget_id = $1 AND user_id = $2",
            budget_id, user_id,
        )
    if result == "DELETE 0":
        raise ApiError("NOT_FOUND")
    await audit("planning.budget_deleted", user_id=user_id, tenant_id=tenant_id, resource="budget", resource_id=budget_id)
    return True


async def create_goal(user_id: str, tenant_id: str, title: str, target_amount: Decimal, target_date: date, priority: int) -> str:
    async with db.with_tenant(tenant_id) as conn:
        goal_id = await conn.fetchval(
            """INSERT INTO goals (user_id, tenant_id, title, target_amount, target_date, current_amount, priority)
               VALUES ($1, $2, $3, $4, $5, 0, $6) RETURNING goal_id""",
            user_id, tenant_id, title, target_amount, target_date, priority,
        )
    await audit("planning.goal_created", user_id=user_id, tenant_id=tenant_id, resource="goal", resource_id=goal_id)
    return goal_id


async def get_goals(user_id: str, tenant_id: str) -> list[dict[str, Any]]:
    async with db.with_tenant(tenant_id) as conn:
        goals = await conn.fetch(
            "SELECT goal_id, title, target_amount, target_date, current_amount, priority, created_at FROM goals WHERE user_id = $1 ORDER BY priority",
            user_id,
        )
    
    result = []
    for g in goals:
        progress_pct = float((g["current_amount"] / g["target_amount"]) * 100) if g["target_amount"] > 0 else 0
        result.append({
            "goal_id": str(g["goal_id"]),
            "title": g["title"],
            "target_amount": g["target_amount"],
            "target_date": g["target_date"].isoformat(),
            "current_amount": g["current_amount"],
            "progress_pct": min(progress_pct, 100),
            "priority": g["priority"],
            "created_at": g["created_at"].isoformat(),
        })
    return result


async def update_goal_progress(user_id: str, tenant_id: str, goal_id: str, current_amount: Decimal) -> dict[str, Any]:
    async with db.with_tenant(tenant_id) as conn:
        goal = await conn.fetchrow(
            "SELECT target_amount, current_amount FROM goals WHERE goal_id = $1 AND user_id = $2",
            goal_id, user_id,
        )
        if not goal:
            raise ApiError("NOT_FOUND")
        
        new_progress_pct = (current_amount / goal["target_amount"]) * 100 if goal["target_amount"] > 0 else 0
        old_progress_pct = (goal["current_amount"] / goal["target_amount"]) * 100 if goal["target_amount"] > 0 else 0
        
        milestones = [25, 50, 75, 100]
        for milestone in milestones:
            if old_progress_pct < milestone <= new_progress_pct:
                await conn.execute(
                    """INSERT INTO goal_milestones (goal_id, milestone_pct, achieved_at)
                       VALUES ($1, $2, NOW()) ON CONFLICT DO NOTHING""",
                    goal_id, milestone,
                )
        
        await conn.execute(
            "UPDATE goals SET current_amount = $1 WHERE goal_id = $2",
            current_amount, goal_id,
        )
    
    await audit("planning.goal_progress_updated", user_id=user_id, tenant_id=tenant_id, resource="goal", resource_id=goal_id, metadata={"progress": str(new_progress_pct)})
    return {"goal_id": str(goal_id), "progress_pct": min(new_progress_pct, 100)}


async def get_debt_accounts(user_id: str, tenant_id: str) -> list[DebtAccountResponse]:
    async with db.with_tenant(tenant_id) as conn:
        accounts = await conn.fetch(
            """SELECT da.debt_id, da.plaid_account_id, da.account_number, da.balance, da.apr, 
                      da.minimum_payment, da.debt_type, da.last_sync_at
               FROM debt_accounts da
               JOIN plaid_items pi ON da.item_id = pi.item_id
               WHERE pi.user_id = $1 ORDER BY da.created_at""",
            user_id,
        )
    
    return [
        DebtAccountResponse(
            debt_id=str(a["debt_id"]),
            plaid_account_id=a["plaid_account_id"],
            account_number=a["account_number"],
            balance=a["balance"],
            apr=a["apr"],
            minimum_payment=a["minimum_payment"],
            debt_type=a["debt_type"],
            last_sync_at=a["last_sync_at"].isoformat() if a["last_sync_at"] else None,
        )
        for a in accounts
    ]


async def get_debt_summary(user_id: str, tenant_id: str) -> DebtSummaryResponse:
    accounts = await get_debt_accounts(user_id, tenant_id)
    
    total_balance = sum(a.balance for a in accounts)
    total_monthly = sum(a.minimum_payment for a in accounts if a.minimum_payment)
    
    if total_balance > 0 and len(accounts) > 0:
        weighted_apr = sum((a.balance * (a.apr or Decimal(0))) for a in accounts) / total_balance
    else:
        weighted_apr = Decimal(0)
    
    return DebtSummaryResponse(
        total_balance=total_balance,
        total_monthly_payment=total_monthly,
        weighted_apr=weighted_apr,
        accounts=accounts,
    )


async def get_portfolio_holdings(user_id: str, tenant_id: str) -> list[HoldingResponse]:
    async with db.with_tenant(tenant_id) as conn:
        holdings = await conn.fetch(
            """SELECT ph.holding_id, ph.plaid_account_id, ph.ticker, ph.quantity, ph.cost_basis,
                      ph.institution_value, ph.last_sync_at
               FROM portfolio_holdings ph
               JOIN plaid_items pi ON ph.item_id = pi.item_id
               WHERE pi.user_id = $1 ORDER BY ph.created_at""",
            user_id,
        )
    
    return [
        HoldingResponse(
            holding_id=str(h["holding_id"]),
            plaid_account_id=h["plaid_account_id"],
            ticker=h["ticker"],
            quantity=h["quantity"],
            cost_basis=h["cost_basis"],
            institution_value=h["institution_value"],
            last_sync_at=h["last_sync_at"].isoformat() if h["last_sync_at"] else None,
        )
        for h in holdings
    ]


async def get_portfolio_summary(user_id: str, tenant_id: str) -> PortfolioSummaryResponse:
    holdings = await get_portfolio_holdings(user_id, tenant_id)
    
    total_value = sum(h.institution_value for h in holdings)
    total_cost = sum(h.cost_basis for h in holdings if h.cost_basis)
    total_gain = total_value - total_cost
    gain_loss_pct = float((total_gain / total_cost) * 100) if total_cost > 0 else 0
    
    return PortfolioSummaryResponse(
        total_value=total_value,
        total_cost_basis=total_cost,
        total_gain_loss=total_gain,
        gain_loss_pct=gain_loss_pct,
        holdings=holdings,
    )
