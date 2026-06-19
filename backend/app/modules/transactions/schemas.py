"""Pydantic models for the transactions API."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class TransactionOut(BaseModel):
    transaction_id: str
    date: date
    merchant_name: str | None
    amount: Decimal           # Plaid convention: positive = money out (spend)
    category: str | None
    pending: bool
    currency_code: str


class TransactionList(BaseModel):
    items: list[TransactionOut]
    limit: int
    offset: int
