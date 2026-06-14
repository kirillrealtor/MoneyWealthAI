"""Debt dashboard routes (auth-gated; compute endpoint rate-limited)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import settings
from app.deps import CurrentUser, rate_limit, require_auth

from . import service
from .schemas import DebtSummary, PayoffComparison, PayoffRequest

router = APIRouter(prefix="/api/v1/debt", tags=["debt"])


@router.get("", response_model=DebtSummary,
            dependencies=[Depends(rate_limit("read", settings.rate_limit_read_per_min))])
async def summary(user: CurrentUser = Depends(require_auth)) -> DebtSummary:
    return DebtSummary(**await service.get_summary(user.user_id, user.tenant_id))


@router.post("/payoff", response_model=PayoffComparison,
             dependencies=[Depends(rate_limit("debt_payoff", settings.rate_limit_general_per_min))])
async def payoff(body: PayoffRequest, user: CurrentUser = Depends(require_auth)) -> PayoffComparison:
    return PayoffComparison(**await service.payoff_comparison(
        user.user_id, user.tenant_id, body.extra_monthly_payment))
