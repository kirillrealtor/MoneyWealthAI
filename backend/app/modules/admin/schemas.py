"""Pydantic models for the admin API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class AdminTokenResponse(BaseModel):
    access_token: str
    role: str


class Kpis(BaseModel):
    total_users: int
    verified_users: int
    suspended_users: int
    signups_today: int
    signups_7d: int
    signups_30d: int
    total_budgets: int
    total_goals: int
    linked_items: int


class AdminUserRow(BaseModel):
    user_id: str
    email: str
    full_name: str | None
    tier: str
    is_verified: bool
    suspended: bool
    created_at: datetime
    last_login_at: datetime | None


class AdminUserList(BaseModel):
    items: list[AdminUserRow]
    limit: int
    offset: int


class AdminUserDetail(BaseModel):
    user_id: str
    email: str
    full_name: str | None
    tier: str
    advisor_persona: str
    is_verified: bool
    suspended: bool
    onboarding_step: int
    created_at: datetime
    last_login_at: datetime | None
    budget_count: int
    goal_count: int
    linked_items: int


class AdminUserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tier: str | None = Field(default=None, pattern="^(free|plus|premium)$")
    suspended: bool | None = None
    is_verified: bool | None = None
    reason: str | None = Field(default=None, max_length=500)  # audited


class AuditRow(BaseModel):
    log_id: str
    user_id: str | None
    action: str
    resource: str | None
    resource_id: str | None
    ip_address: str | None
    ts: datetime


class AuditList(BaseModel):
    items: list[AuditRow]
    limit: int
    offset: int


class MessageResponse(BaseModel):
    message: str
