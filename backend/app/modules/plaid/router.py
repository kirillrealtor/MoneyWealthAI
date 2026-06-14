"""Plaid HTTP routes.

Security: link/exchange/disconnect require an authenticated AND email-verified
user (financial actions), and are rate-limited. The webhook endpoint is
unauthenticated by nature but is trusted ONLY after cryptographic signature
verification.
"""
from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.deps import CurrentUser, rate_limit, require_auth, require_verified
from app.errors import ApiError

from . import service
from .schemas import (
    ExchangeRequest,
    ExchangeResponse,
    ItemSummary,
    LinkTokenResponse,
    MessageResponse,
)
from .webhook import dispatch_webhook, verify_webhook

router = APIRouter(prefix="/api/v1/plaid", tags=["plaid"])
webhook_router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/link-token", response_model=LinkTokenResponse,
             dependencies=[Depends(rate_limit("plaid_link", 30))])
async def link_token(user: CurrentUser = Depends(require_verified)) -> LinkTokenResponse:
    result = await service.create_link_token(user.user_id)
    return LinkTokenResponse(**result)


@router.post("/exchange", response_model=ExchangeResponse,
             dependencies=[Depends(rate_limit("plaid_exchange", 30))])
async def exchange(body: ExchangeRequest, request: Request,
                   user: CurrentUser = Depends(require_verified)) -> ExchangeResponse:
    result = await service.exchange_public_token(user.user_id, user.tenant_id, body.public_token, _ip(request))
    return ExchangeResponse(**result)


@router.get("/items", response_model=list[ItemSummary],
            dependencies=[Depends(rate_limit("read", settings.rate_limit_read_per_min))])
async def list_items(user: CurrentUser = Depends(require_auth)) -> list[ItemSummary]:
    items = await service.list_items(user.user_id, user.tenant_id)
    return [ItemSummary(**it) for it in items]


@router.delete("/items/{item_id}", response_model=MessageResponse)
async def disconnect(item_id: UUID, request: Request,
                     user: CurrentUser = Depends(require_verified)) -> MessageResponse:
    await service.disconnect_item(user.user_id, user.tenant_id, str(item_id), _ip(request))
    return MessageResponse(message="Bank connection removed.")


@webhook_router.post("/plaid", status_code=200,
                     dependencies=[Depends(rate_limit("plaid_webhook", 600))])
async def plaid_webhook(request: Request) -> dict[str, str]:
    raw = await request.body()
    header = request.headers.get("plaid-verification")
    if not await verify_webhook(raw, header):
        raise ApiError("UNAUTHORIZED", message="Webhook signature verification failed.")
    try:
        payload = json.loads(raw)
    except ValueError as err:
        raise ApiError("VALIDATION_ERROR", message="Invalid webhook body.") from err
    await dispatch_webhook(payload)
    return {"status": "ok"}
