"""Billing routes (Stripe Checkout + Customer Portal) and the Stripe webhook."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app import db
from app.deps import CurrentUser, require_auth, require_verified

from . import service
from .schemas import CheckoutRequest, SubscriptionOut, UrlResponse

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])
webhook_router = APIRouter(prefix="/api/v1/webhooks", tags=["billing"])


@router.post("/checkout", response_model=UrlResponse)
async def checkout(body: CheckoutRequest, user: CurrentUser = Depends(require_verified)) -> UrlResponse:
    async with db.with_tenant(user.tenant_id, user.user_id) as conn:
        email = await conn.fetchval("SELECT email FROM users WHERE user_id = $1", user.user_id)
    url = await service.create_checkout(user.user_id, user.tenant_id, email, body.plan, body.interval)
    return UrlResponse(url=url)


@router.post("/portal", response_model=UrlResponse)
async def portal(user: CurrentUser = Depends(require_auth)) -> UrlResponse:
    url = await service.create_portal(user.user_id, user.tenant_id)
    return UrlResponse(url=url)


@router.get("/subscription", response_model=SubscriptionOut | None)
async def subscription(user: CurrentUser = Depends(require_auth)) -> SubscriptionOut | None:
    sub = await service.get_subscription(user.user_id, user.tenant_id)
    return SubscriptionOut(**sub) if sub else None


@webhook_router.post("/stripe")
async def stripe_webhook(request: Request) -> dict[str, bool]:
    payload = await request.body()
    await service.handle_webhook(payload, request.headers.get("stripe-signature"))
    return {"received": True}
