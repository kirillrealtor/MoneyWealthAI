"""Budgets HTTP routes (auth-gated)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.config import settings
from app.deps import CurrentUser, rate_limit, require_auth

from . import service
from .schemas import BudgetCreate, BudgetStatus, BudgetUpdate, MessageResponse

router = APIRouter(prefix="/api/v1/budgets", tags=["budgets"])
# Per-user throttle for cheap authenticated reads (anti-scraping on unmetered GETs).
_read_limit = Depends(rate_limit("read", settings.rate_limit_read_per_min))


@router.post("", response_model=BudgetStatus, status_code=201)
async def create(body: BudgetCreate, user: CurrentUser = Depends(require_auth)) -> BudgetStatus:
    await service.create_budget(
        user.user_id, user.tenant_id,
        category=body.category, monthly_limit=body.monthly_limit, alert_at_pct=body.alert_at_pct,
    )
    statuses = await service.list_status(user.user_id, user.tenant_id)
    created = next(s for s in statuses if s["category"] == body.category)
    return BudgetStatus(**created)


@router.get("", response_model=list[BudgetStatus], dependencies=[_read_limit])
async def list_budgets(user: CurrentUser = Depends(require_auth)) -> list[BudgetStatus]:
    return [BudgetStatus(**s) for s in await service.list_status(user.user_id, user.tenant_id)]


@router.patch("/{budget_id}", response_model=MessageResponse)
async def update(budget_id: UUID, body: BudgetUpdate,
                 user: CurrentUser = Depends(require_auth)) -> MessageResponse:
    await service.update_budget(
        user.user_id, user.tenant_id, str(budget_id),
        monthly_limit=body.monthly_limit, alert_at_pct=body.alert_at_pct, is_active=body.is_active,
    )
    return MessageResponse(message="Budget updated.")


@router.delete("/{budget_id}", response_model=MessageResponse)
async def delete(budget_id: UUID, user: CurrentUser = Depends(require_auth)) -> MessageResponse:
    await service.delete_budget(user.user_id, user.tenant_id, str(budget_id))
    return MessageResponse(message="Budget deleted.")
