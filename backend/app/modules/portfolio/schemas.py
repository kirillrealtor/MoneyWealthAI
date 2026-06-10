"""Pydantic models for the portfolio dashboard (data-only; educational)."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HoldingOut(BaseModel):
    name: str | None
    ticker: str | None
    asset_class: str | None
    sector: str | None
    value: Decimal | None
    unrealized_gain_loss: Decimal | None


class PortfolioSummary(BaseModel):
    total_value: Decimal
    unrealized_gain_loss: Decimal
    allocation_pct: dict[str, float]
    sector_exposure_pct: dict[str, float]
    concentration_flags: list[str]
    top_holdings: list[HoldingOut]
    note: str | None


class RebalanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_allocation: dict[str, float] = Field(min_length=1)

    @field_validator("target_allocation")
    @classmethod
    def _validate(cls, v: dict[str, float]) -> dict[str, float]:
        if any(p < 0 or p > 100 for p in v.values()):
            raise ValueError("each target percentage must be between 0 and 100")
        if not (99.0 <= sum(v.values()) <= 101.0):
            raise ValueError("target percentages must sum to ~100")
        return v


class RebalanceGap(BaseModel):
    asset_class: str
    current_pct: float
    target_pct: float
    drift_pct: float
    current_value: Decimal
    target_value: Decimal
    adjustment_value: Decimal  # +ve = under-allocated (add), -ve = over-allocated


class RebalanceResponse(BaseModel):
    total_value: Decimal
    gaps: list[RebalanceGap]
    note: str
