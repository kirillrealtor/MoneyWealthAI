"""Portfolio dashboard routes (auth-gated; rebalance compute rate-limited)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import settings
from app.deps import CurrentUser, rate_limit, require_auth

from . import service
from .schemas import PortfolioSummary, RebalanceRequest, RebalanceResponse

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioSummary)
async def summary(user: CurrentUser = Depends(require_auth)) -> PortfolioSummary:
    return PortfolioSummary(**await service.get_summary(user.user_id, user.tenant_id))


@router.post("/rebalance", response_model=RebalanceResponse,
             dependencies=[Depends(rate_limit("portfolio_rebalance", settings.rate_limit_general_per_min))])
async def rebalance(body: RebalanceRequest, user: CurrentUser = Depends(require_auth)) -> RebalanceResponse:
    return RebalanceResponse(**await service.rebalance_gaps(
        user.user_id, user.tenant_id, body.target_allocation))
