"""Affordability calculator. Pure/Decimal.

Recurring purchase -> impact on monthly surplus and debt-to-income.
One-time purchase -> impact on liquidity / emergency fund.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

_DTI_CAUTION = Decimal("0.36")  # standard lending threshold
_EMERGENCY_MONTHS = Decimal("3")  # < 3 months of spend left = flag


@dataclass
class AffordabilityResult:
    recommendation_flag: str               # "ok" | "caution"
    post_purchase_surplus: Decimal | None  # recurring only
    dti_after: Decimal | None              # recurring only
    post_purchase_liquid: Decimal | None   # one-time only
    emergency_fund_flag: bool


def calculate_affordability(
    *,
    purchase_amount: Decimal,
    is_recurring: bool,
    monthly_payment_estimate: Decimal = Decimal("0"),
    liquid_assets: Decimal = Decimal("0"),
    monthly_surplus: Decimal = Decimal("0"),
    monthly_spend: Decimal = Decimal("0"),
    current_dti: Decimal = Decimal("0"),
    monthly_income: Decimal = Decimal("0"),
) -> AffordabilityResult:
    if is_recurring:
        if monthly_payment_estimate <= 0:
            # Can't assess a recurring purchase without its monthly payment.
            return AffordabilityResult("insufficient_data", None, None, None, False)
        post_surplus = monthly_surplus - monthly_payment_estimate
        dti_after = current_dti
        if monthly_income > 0:
            dti_after = current_dti + (monthly_payment_estimate / monthly_income)
        flag = "caution" if (dti_after > _DTI_CAUTION or post_surplus < 0) else "ok"
        return AffordabilityResult(flag, post_surplus.quantize(Decimal("0.01")),
                                   dti_after.quantize(Decimal("0.0001")), None, post_surplus < 0)

    # One-time purchase.
    post_liquid = liquid_assets - purchase_amount
    emergency_floor = monthly_spend * _EMERGENCY_MONTHS
    emergency_flag = post_liquid < emergency_floor
    flag = "caution" if (post_liquid < 0 or emergency_flag) else "ok"
    return AffordabilityResult(flag, None, None, post_liquid.quantize(Decimal("0.01")), emergency_flag)
