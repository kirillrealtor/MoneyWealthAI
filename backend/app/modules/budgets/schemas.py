"""Pydantic models for the budgets API."""
from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.money import MONEY_MAX

PLAID_CATEGORIES = Literal[
    "FOOD_AND_DRINK", "SHOPPING", "ENTERTAINMENT", "TRANSPORTATION",
    "TRAVEL", "TRANSFER", "FEES", "TAXES", "LOANS_AND_MORTGAGES",
    "BANK_FEES", "FINANCIAL", "PERSONAL_FINANCE", "UNCATEGORIZED", "PERSONAL",
]


class BudgetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: PLAID_CATEGORIES
    monthly_limit: Decimal = Field(gt=0, le=MONEY_MAX)
    alert_at_pct: int = Field(default=80, ge=1, le=100)


class BudgetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    monthly_limit: Decimal | None = Field(default=None, gt=0, le=MONEY_MAX)
    alert_at_pct: int | None = Field(default=None, ge=1, le=100)
    is_active: bool | None = None


class BudgetStatus(BaseModel):
    budget_id: str
    category: str
    monthly_limit: Decimal
    spent: Decimal
    pct_used: float
    remaining: Decimal
    alert_at_pct: int
    is_active: bool


class MessageResponse(BaseModel):
    message: str
