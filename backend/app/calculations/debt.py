"""Debt payoff calculator (snowball vs avalanche). Pure, Decimal-exact, no I/O.

Month-by-month simulation with a fixed monthly budget (sum of minimums + extra).
Minimums are paid on every active debt; the remainder goes to the *target* debt
(highest APR for avalanche, lowest balance for snowball). As debts clear, their
freed minimum rolls into the remainder — the classic snowball effect.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

_CENT = Decimal("0.01")
_MAX_MONTHS = 1200  # 100-year guard against negative amortization


@dataclass(frozen=True)
class Debt:
    id: str
    balance: Decimal
    apr: Decimal            # annual, e.g. Decimal("0.2499")
    minimum_payment: Decimal


@dataclass
class PayoffPlan:
    method: str
    payoff_order: list[str]
    months_to_payoff: int
    total_interest: Decimal
    feasible: bool


def _money(x: Decimal) -> Decimal:
    return x.quantize(_CENT)


def _simulate(debts: list[Debt], extra: Decimal, method: str, order: list[str]) -> PayoffPlan:
    bal = {d.id: d.balance for d in debts if d.balance > 0}
    minimum = {d.id: d.minimum_payment for d in debts}
    apr = {d.id: d.apr for d in debts}
    if not bal:
        return PayoffPlan(method, [], 0, Decimal("0.00"), True)

    monthly_budget = sum((minimum[i] for i in bal), Decimal("0")) + extra
    total_interest = Decimal("0")
    payoff_seq: list[str] = []
    months = 0

    while bal and months < _MAX_MONTHS:
        months += 1
        start_total = sum(bal.values(), Decimal("0"))
        # 1. Accrue interest on active debts.
        for i in list(bal):
            interest = bal[i] * apr[i] / Decimal("12")
            bal[i] += interest
            total_interest += interest
        # 2. Pay minimums (capped at balance/remaining), then funnel remainder to target.
        remaining = monthly_budget
        for i in order:
            if i in bal and remaining > 0:
                pay = min(minimum[i], bal[i], remaining)
                bal[i] -= pay
                remaining -= pay
        for i in order:  # remainder to the highest-priority active debt
            if i in bal and remaining > 0:
                pay = min(remaining, bal[i])
                bal[i] -= pay
                remaining -= pay
        # 3. Stall detection: if total principal didn't drop, the payment can't
        #    cover the interest -> it never amortizes. Bail fast (no 1,200-month
        #    spin that would block the event loop) and report infeasible.
        if sum(bal.values(), Decimal("0")) >= start_total - _CENT:
            break
        # 4. Retire any cleared debts (preserve payoff order).
        for i in order:
            if i in bal and bal[i] <= _CENT:
                payoff_seq.append(i)
                del bal[i]

    feasible = not bal  # everything cleared within the month cap
    for i in order:  # any still-unpaid debts append at the end
        if i in bal:
            payoff_seq.append(i)
    return PayoffPlan(method, payoff_seq, months, _money(total_interest), feasible)


def calculate_debt_payoff(debts: list[Debt], extra_monthly_payment: Decimal = Decimal("0")) -> dict[str, PayoffPlan]:
    active = [d for d in debts if d.balance > 0]
    avalanche_order = [d.id for d in sorted(active, key=lambda d: d.apr, reverse=True)]
    snowball_order = [d.id for d in sorted(active, key=lambda d: d.balance)]
    return {
        "avalanche": _simulate(debts, extra_monthly_payment, "avalanche", avalanche_order),
        "snowball": _simulate(debts, extra_monthly_payment, "snowball", snowball_order),
    }


def debt_to_income(total_monthly_debt_payments: Decimal, monthly_income: Decimal) -> Decimal | None:
    if monthly_income <= 0:
        return None
    return (total_monthly_debt_payments / monthly_income).quantize(Decimal("0.0001"))


def months_at_minimum(balance: Decimal, apr: Decimal, minimum_payment: Decimal) -> int | None:
    """Months to clear a single debt paying only its minimum. None = never pays
    off (minimum doesn't cover the monthly interest -> negative amortization)."""
    if balance <= 0:
        return 0
    if minimum_payment <= 0:
        return None
    rate = apr / Decimal("12")
    # O(1) non-amortization check: if the first month's interest already meets or
    # exceeds the payment, the balance only grows -> never pays off. Avoids a
    # 1,200-iteration spin in the request path.
    if minimum_payment <= balance * rate:
        return None
    bal = balance
    for month in range(1, _MAX_MONTHS + 1):
        bal += bal * rate
        bal -= minimum_payment
        if bal <= _CENT:
            return month
    return None
