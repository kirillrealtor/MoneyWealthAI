"""Pydantic models for the debt dashboard."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DebtOut(BaseModel):
    debt_id: str
    debt_type: str | None
    balance: Decimal | None
    apr: Decimal | None
    minimum_payment: Decimal | None
    months_at_minimum: int | None
    above_typical_rate: bool


class DebtSummary(BaseModel):
    debts: list[DebtOut]
    total_debt: Decimal
    total_minimum_payment: Decimal
    debt_to_income: float | None
    note: str | None


class PayoffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    extra_monthly_payment: Decimal = Field(default=Decimal("0"), ge=0)


class PayoffMethod(BaseModel):
    payoff_order: list[str]
    months_to_payoff: int
    total_interest: Decimal
    feasible: bool


class PayoffComparison(BaseModel):
    avalanche: PayoffMethod
    snowball: PayoffMethod
    interest_saved_with_avalanche: Decimal
    note: str | None
