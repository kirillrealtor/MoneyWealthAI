"""Pydantic models for the billing API."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class CheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan: Literal["plus", "premium"]
    interval: Literal["monthly", "annual"]


class UrlResponse(BaseModel):
    url: str


class SubscriptionOut(BaseModel):
    tier: str
    status: str
    current_period_end: datetime | None
    cancel_at_period_end: bool
