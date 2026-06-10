"""Goal reverse-engineering: turn a target into a monthly savings number,
flag feasibility, and propose an extended timeline if needed. Pure/Decimal."""
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal

_CENT = Decimal("0.01")


@dataclass
class GoalPlan:
    monthly_target: Decimal
    feasible: bool
    months_remaining: int
    extended_timeline_months: int | None  # if infeasible, months needed at the surplus


def reverse_engineer_goal(
    *,
    target_amount: Decimal,
    current_amount: Decimal,
    months_remaining: int,
    available_monthly_surplus: Decimal | None = None,
    inflation_rate: Decimal = Decimal("0"),
) -> GoalPlan:
    remaining = max(target_amount - current_amount, Decimal("0"))
    months = max(months_remaining, 1)

    base = remaining / Decimal(months)
    # Mild inflation adjustment over half the horizon (matches blueprint formula).
    if inflation_rate > 0:
        years_half = Decimal(months) / Decimal("24")
        factor = Decimal(str((1 + float(inflation_rate)) ** float(years_half)))
        monthly = base * factor
    else:
        monthly = base

    feasible = available_monthly_surplus is None or monthly <= available_monthly_surplus
    extended: int | None = None
    if not feasible and available_monthly_surplus and available_monthly_surplus > 0:
        extended = math.ceil(float(remaining / available_monthly_surplus))

    return GoalPlan(monthly.quantize(_CENT), feasible, months, extended)
