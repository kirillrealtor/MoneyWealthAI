"""Goal business logic — reverse-engineers a monthly target on create and
reports progress / on-track status. Tenant-scoped (RLS)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from app import db
from app.calculations.goals import reverse_engineer_goal
from app.errors import ApiError


def _months_until(target: date) -> int:
    today = date.today()
    return max((target.year - today.year) * 12 + (target.month - today.month), 1)


async def create_goal(
    user_id: str, tenant_id: str, *, title: str, description: str | None,
    target_amount: Decimal, current_amount: Decimal, target_date: date, priority: int,
) -> str:
    plan = reverse_engineer_goal(
        target_amount=target_amount, current_amount=current_amount,
        months_remaining=_months_until(target_date),
    )
    async with db.with_tenant(tenant_id) as conn:
        return str(await conn.fetchval(
            """INSERT INTO goals
                   (user_id, tenant_id, title, description, target_amount, current_amount,
                    target_date, monthly_target, priority)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) RETURNING goal_id""",
            user_id, tenant_id, title, description, target_amount, current_amount,
            target_date, plan.monthly_target, priority,
        ))


def _to_out(row: Any) -> dict[str, Any]:
    target = row["target_amount"]
    current = row["current_amount"]
    progress = float(current / target * 100) if target > 0 else 0.0
    months = _months_until(row["target_date"])
    # Quantize to cents so a fresh goal (required_now == stored monthly_target)
    # isn't marked off-track by a sub-cent rounding difference.
    required_now = (
        ((target - current) / Decimal(months)).quantize(Decimal("0.01")) if current < target else Decimal("0")
    )
    original = row["monthly_target"] or required_now
    on_track = row["status"] == "completed" or current >= target or required_now <= original
    return {
        "goal_id": str(row["goal_id"]), "title": row["title"], "description": row["description"],
        "target_amount": target, "current_amount": current, "target_date": row["target_date"],
        "monthly_target": row["monthly_target"], "progress_pct": round(progress, 1),
        "on_track": bool(on_track), "status": row["status"], "priority": row["priority"],
    }


async def list_goals(user_id: str, tenant_id: str) -> list[dict[str, Any]]:
    async with db.with_tenant(tenant_id) as conn:
        rows = await conn.fetch(
            """SELECT goal_id, title, description, target_amount, current_amount, target_date,
                      monthly_target, status, priority
                 FROM goals WHERE user_id = $1 ORDER BY priority, created_at""",
            user_id,
        )
    return [_to_out(r) for r in rows]


async def update_goal(
    user_id: str, tenant_id: str, goal_id: str,
    *, title: str | None, target_amount: Decimal | None, current_amount: Decimal | None,
    target_date: date | None, priority: int | None, status: str | None,
) -> None:
    async with db.with_tenant(tenant_id) as conn:
        result = await conn.execute(
            """UPDATE goals SET
                   title = COALESCE($3, title),
                   target_amount = COALESCE($4, target_amount),
                   current_amount = COALESCE($5, current_amount),
                   target_date = COALESCE($6, target_date),
                   priority = COALESCE($7, priority),
                   status = COALESCE($8, status)
                WHERE goal_id = $1 AND user_id = $2""",
            goal_id, user_id, title, target_amount, current_amount, target_date, priority, status,
        )
    if result.split()[-1] == "0":  # "UPDATE 0" / "DELETE 0" -> no row matched
        raise ApiError("NOT_FOUND")


async def delete_goal(user_id: str, tenant_id: str, goal_id: str) -> None:
    async with db.with_tenant(tenant_id) as conn:
        result = await conn.execute(
            "DELETE FROM goals WHERE goal_id = $1 AND user_id = $2", goal_id, user_id
        )
    if result.split()[-1] == "0":  # "UPDATE 0" / "DELETE 0" -> no row matched
        raise ApiError("NOT_FOUND")
