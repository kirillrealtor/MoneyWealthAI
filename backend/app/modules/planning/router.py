from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends

from app.deps import CurrentUser, require_auth, resolve_tenant

from . import service
from .schemas import BudgetRequest, BudgetResponse, DebtSummaryResponse, GoalRequest, GoalResponse, PortfolioSummaryResponse

router = APIRouter(prefix="/api/v1/planning", tags=["planning"], dependencies=[Depends(require_auth)])


@router.post("/budgets", response_model=dict[str, str], status_code=201)
async def create_budget(
    body: BudgetRequest,
    user: CurrentUser = Depends(),
    tenant_id: str = Depends(resolve_tenant),
) -> dict[str, str]:
    budget_id = await service.create_budget(
        user_id=user["user_id"],
        tenant_id=tenant_id,
        category=body.category,
        monthly_limit=body.monthly_limit,
        alert_at_pct=body.alert_at_pct,
    )
    return {"budget_id": budget_id}


@router.get("/budgets", response_model=list[BudgetResponse])
async def list_budgets(
    user: CurrentUser = Depends(),
    tenant_id: str = Depends(resolve_tenant),
) -> list[BudgetResponse]:
    return await service.get_budgets(user_id=user["user_id"], tenant_id=tenant_id)


@router.patch("/budgets/{budget_id}", response_model=dict[str, str])
async def update_budget(
    budget_id: str,
    body: BudgetRequest,
    user: CurrentUser = Depends(),
    tenant_id: str = Depends(resolve_tenant),
) -> dict[str, str]:
    await service.update_budget(
        user_id=user["user_id"],
        tenant_id=tenant_id,
        budget_id=budget_id,
        monthly_limit=body.monthly_limit,
    )
    return {"message": "Budget updated"}


@router.delete("/budgets/{budget_id}", response_model=dict[str, str])
async def delete_budget(
    budget_id: str,
    user: CurrentUser = Depends(),
    tenant_id: str = Depends(resolve_tenant),
) -> dict[str, str]:
    await service.delete_budget(user_id=user["user_id"], tenant_id=tenant_id, budget_id=budget_id)
    return {"message": "Budget deleted"}


@router.post("/goals", response_model=dict[str, str], status_code=201)
async def create_goal(
    body: GoalRequest,
    user: CurrentUser = Depends(),
    tenant_id: str = Depends(resolve_tenant),
) -> dict[str, str]:
    goal_id = await service.create_goal(
        user_id=user["user_id"],
        tenant_id=tenant_id,
        title=body.title,
        target_amount=body.target_amount,
        target_date=body.target_date,
        priority=body.priority,
    )
    return {"goal_id": goal_id}


@router.get("/goals", response_model=list[GoalResponse])
async def list_goals(
    user: CurrentUser = Depends(),
    tenant_id: str = Depends(resolve_tenant),
) -> list[dict[str, Any]]:
    return await service.get_goals(user_id=user["user_id"], tenant_id=tenant_id)


@router.patch("/goals/{goal_id}/progress", response_model=dict[str, Any])
async def update_goal_progress(
    goal_id: str,
    body: dict[str, Decimal],
    user: CurrentUser = Depends(),
    tenant_id: str = Depends(resolve_tenant),
) -> dict[str, Any]:
    return await service.update_goal_progress(
        user_id=user["user_id"],
        tenant_id=tenant_id,
        goal_id=goal_id,
        current_amount=body["current_amount"],
    )


@router.get("/debt", response_model=DebtSummaryResponse)
async def get_debt_dashboard(
    user: CurrentUser = Depends(),
    tenant_id: str = Depends(resolve_tenant),
) -> DebtSummaryResponse:
    return await service.get_debt_summary(user_id=user["user_id"], tenant_id=tenant_id)


@router.get("/portfolio", response_model=PortfolioSummaryResponse)
async def get_portfolio_dashboard(
    user: CurrentUser = Depends(),
    tenant_id: str = Depends(resolve_tenant),
) -> PortfolioSummaryResponse:
    return await service.get_portfolio_summary(user_id=user["user_id"], tenant_id=tenant_id)