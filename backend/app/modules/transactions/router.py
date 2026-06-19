"""Transactions HTTP routes (read-only, rate-limited reads)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.config import settings
from app.deps import CurrentUser, rate_limit, require_auth

from . import service
from .schemas import TransactionList, TransactionOut

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.get("", response_model=TransactionList,
            dependencies=[Depends(rate_limit("read", settings.rate_limit_read_per_min))])
async def list_transactions(
    user: CurrentUser = Depends(require_auth),
    category: str | None = Query(default=None, max_length=100),
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> TransactionList:
    rows = await service.list_transactions(
        user.user_id, user.tenant_id, limit=limit, offset=offset, category=category, search=search,
    )
    return TransactionList(items=[TransactionOut(**r) for r in rows], limit=limit, offset=offset)
