from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


PLAID_CATEGORIES = Literal[
    "FOOD_AND_DRINK", "SHOPPING", "TRANSPORTATION", "TRAVEL",
    "TRANSFER", "INCOME", "TAXES", "ENTERTAINMENT", "PERSONAL",
    "UNCATEGORIZED", "BANK_FEES", "CABLE_SATELLITE", "EDUCATION",
    "FAST_FOOD", "GAS", "GROCERIES", "GYMS_AND_FITNESS",
    "HAIR", "HOBBIES", "HOME", "HOTELS", "INSURANCE", "INTERNET",
    "LOAN", "MOBILE_PHONE", "MOVIES", "MUSIC", "NEWSPAPERS",
    "OFFICE_SUPPLIES", "PHARMACY", "RESTAURANTS", "SUBSCRIPTIONS",
    "UTILITIES", "VETERINARY"
]


class BudgetRequest(BaseModel):
    category: PLAID_CATEGORIES
    monthly_limit: Decimal = Field(..., gt=0)
    alert_at_pct: int = Field(80, ge=1, le=100)


class BudgetResponse(BaseModel):
    budget_id: str
    category: str
    monthly_limit: Decimal
    spent_this_month: Decimal
    alert_at_pct: int
    created_at: str


class GoalRequest(BaseModel):
    title: str = Field(..., max_length=255)
    target_amount: Decimal = Field(..., gt=0)
    target_date: date
    priority: int = Field(1, ge=1, le=5)


class GoalResponse(BaseModel):
    goal_id: str
    title: str
    target_amount: Decimal
    target_date: date
    current_amount: Decimal
    progress_pct: float
    priority: int
    created_at: str


class DebtAccountResponse(BaseModel):
    debt_id: str
    plaid_account_id: str
    account_number: str | None
    balance: Decimal
    apr: Decimal | None
    minimum_payment: Decimal | None
    debt_type: str
    last_sync_at: str


class DebtSummaryResponse(BaseModel):
    total_balance: Decimal
    total_monthly_payment: Decimal
    weighted_apr: Decimal
    accounts: list[DebtAccountResponse]


class HoldingResponse(BaseModel):
    holding_id: str
    plaid_account_id: str
    ticker: str
    quantity: Decimal
    cost_basis: Decimal | None
    institution_value: Decimal
    last_sync_at: str


class PortfolioSummaryResponse(BaseModel):
    total_value: Decimal
    total_cost_basis: Decimal
    total_gain_loss: Decimal
    gain_loss_pct: float
    holdings: list[HoldingResponse]
