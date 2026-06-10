"""Exact unit tests for the financial calculation engine (pure, no I/O)."""
from __future__ import annotations

from decimal import Decimal

from app.calculations.affordability import calculate_affordability
from app.calculations.debt import Debt, calculate_debt_payoff, debt_to_income, months_at_minimum
from app.calculations.goals import reverse_engineer_goal

_DEBTS = [
    Debt("cc", Decimal("5000"), Decimal("0.2499"), Decimal("125")),
    Debt("student", Decimal("12000"), Decimal("0.0599"), Decimal("220")),
    Debt("personal", Decimal("3500"), Decimal("0.1899"), Decimal("85")),
]


def test_avalanche_targets_highest_apr_first() -> None:
    # With extra to funnel, avalanche clears the highest-APR debt first.
    plan = calculate_debt_payoff(_DEBTS, Decimal("300"))
    assert plan["avalanche"].payoff_order[0] == "cc"  # 24.99% APR


def test_snowball_targets_lowest_balance_first() -> None:
    plan = calculate_debt_payoff(_DEBTS, Decimal("300"))
    assert plan["snowball"].payoff_order[0] == "personal"  # $3,500


def test_avalanche_costs_no_more_interest_than_snowball() -> None:
    plan = calculate_debt_payoff(_DEBTS, Decimal("200"))
    assert plan["avalanche"].total_interest <= plan["snowball"].total_interest


def test_extra_payment_shortens_payoff() -> None:
    base = calculate_debt_payoff(_DEBTS, Decimal("0"))["avalanche"].months_to_payoff
    faster = calculate_debt_payoff(_DEBTS, Decimal("300"))["avalanche"].months_to_payoff
    assert faster < base


def test_payoff_flags_infeasible_and_bails_fast() -> None:
    # Minimum ($50) far below monthly interest ($125) -> never amortizes.
    debts = [Debt("cc", Decimal("5000"), Decimal("0.30"), Decimal("50"))]
    plan = calculate_debt_payoff(debts, Decimal("0"))
    assert plan["avalanche"].feasible is False
    assert plan["avalanche"].months_to_payoff < 1200  # bailed via stall detection, not the cap


def test_zero_balance_debt_is_ignored() -> None:
    debts = [*_DEBTS, Debt("paid", Decimal("0"), Decimal("0.15"), Decimal("0"))]
    plan = calculate_debt_payoff(debts, Decimal("100"))
    assert "paid" not in plan["avalanche"].payoff_order


def test_months_at_minimum() -> None:
    assert months_at_minimum(Decimal("1000"), Decimal("0"), Decimal("100")) == 10
    assert months_at_minimum(Decimal("0"), Decimal("0.2"), Decimal("100")) == 0
    # Minimum below monthly interest -> never amortizes.
    assert months_at_minimum(Decimal("5000"), Decimal("0.30"), Decimal("50")) is None


def test_dti() -> None:
    assert debt_to_income(Decimal("900"), Decimal("5000")) == Decimal("0.1800")
    assert debt_to_income(Decimal("900"), Decimal("0")) is None


def test_goal_monthly_target_exact() -> None:
    plan = reverse_engineer_goal(target_amount=Decimal("80000"), current_amount=Decimal("5000"),
                                 months_remaining=36)
    assert plan.monthly_target == Decimal("2083.33")  # 75000 / 36


def test_goal_infeasible_proposes_longer_timeline() -> None:
    plan = reverse_engineer_goal(target_amount=Decimal("80000"), current_amount=Decimal("0"),
                                 months_remaining=12, available_monthly_surplus=Decimal("1000"))
    assert plan.feasible is False
    assert plan.extended_timeline_months is not None and plan.extended_timeline_months > 12


def test_goal_inflation_raises_target() -> None:
    no_infl = reverse_engineer_goal(target_amount=Decimal("50000"), current_amount=Decimal("0"),
                                    months_remaining=24, inflation_rate=Decimal("0"))
    with_infl = reverse_engineer_goal(target_amount=Decimal("50000"), current_amount=Decimal("0"),
                                      months_remaining=24, inflation_rate=Decimal("0.03"))
    assert with_infl.monthly_target > no_infl.monthly_target


def test_affordability_recurring_flags_high_dti() -> None:
    r = calculate_affordability(purchase_amount=Decimal("45000"), is_recurring=True,
                                monthly_payment_estimate=Decimal("750"), monthly_surplus=Decimal("900"),
                                current_dti=Decimal("0.22"), monthly_income=Decimal("5000"))
    assert r.recommendation_flag == "caution"
    assert r.dti_after is not None and r.dti_after > Decimal("0.36")


def test_affordability_recurring_without_estimate_is_insufficient() -> None:
    r = calculate_affordability(purchase_amount=Decimal("35000"), is_recurring=True,
                                monthly_payment_estimate=Decimal("0"), monthly_income=Decimal("5000"))
    assert r.recommendation_flag == "insufficient_data"  # not a misleading "ok"


def test_affordability_lump_flags_emergency_fund() -> None:
    r = calculate_affordability(purchase_amount=Decimal("12000"), is_recurring=False,
                                liquid_assets=Decimal("14000"), monthly_spend=Decimal("4000"))
    assert r.emergency_fund_flag is True
