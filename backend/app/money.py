"""Shared money-input bound.

The tightest money column in the schema is NUMERIC(10,2) (budgets.monthly_limit,
goals.monthly_target, debt minimum_payment). Capping every *user-supplied* money
value to what fits there means a value can never overflow that column or any
value derived from it — closing an unhandled-500 path (asyncpg
NumericValueOutOfRangeError) found in pentest. $99,999,999.99 is far above any
real personal-finance figure, so the cap is invisible to legitimate users.
"""
from __future__ import annotations

from decimal import Decimal

MONEY_MAX = Decimal("99999999.99")
