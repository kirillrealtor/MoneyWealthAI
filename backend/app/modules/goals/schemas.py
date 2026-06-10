"""Pydantic models for the goals API."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class GoalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    target_amount: Decimal = Field(gt=0)
    current_amount: Decimal = Field(default=Decimal("0"), ge=0)
    target_date: date
    priority: int = Field(default=1, ge=1)


class GoalUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=255)
    target_amount: Decimal | None = Field(default=None, gt=0)
    current_amount: Decimal | None = Field(default=None, ge=0)
    target_date: date | None = None
    priority: int | None = Field(default=None, ge=1)
    status: str | None = Field(default=None, pattern="^(active|paused|completed)$")


class GoalOut(BaseModel):
    goal_id: str
    title: str
    description: str | None
    target_amount: Decimal
    current_amount: Decimal
    target_date: date
    monthly_target: Decimal | None
    progress_pct: float
    on_track: bool
    status: str
    priority: int


class MessageResponse(BaseModel):
    message: str
