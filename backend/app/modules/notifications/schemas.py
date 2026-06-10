"""Pydantic models for the notifications API."""
from __future__ import annotations

from datetime import datetime, time

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    alert_id: str
    type: str
    title: str | None
    body: str | None
    severity: str
    is_read: bool
    created_at: datetime


class NotificationList(BaseModel):
    items: list[NotificationOut]
    unread_count: int


class PreferencesOut(BaseModel):
    push_enabled: bool
    email_enabled: bool
    sms_opt_in: bool
    budget_alerts: bool
    goal_alerts: bool
    bank_error_alerts: bool
    unusual_tx_alerts: bool
    weekly_digest: bool
    monthly_report: bool
    marketing_emails: bool
    quiet_hours_start: time
    quiet_hours_end: time
    timezone: str


class PreferencesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    push_enabled: bool | None = None
    email_enabled: bool | None = None
    sms_opt_in: bool | None = None
    budget_alerts: bool | None = None
    goal_alerts: bool | None = None
    bank_error_alerts: bool | None = None
    unusual_tx_alerts: bool | None = None
    weekly_digest: bool | None = None
    monthly_report: bool | None = None
    marketing_emails: bool | None = None
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None
    timezone: str | None = None


class MessageResponse(BaseModel):
    message: str
