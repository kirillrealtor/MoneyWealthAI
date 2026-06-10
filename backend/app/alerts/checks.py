"""Per-user alert checks. Each returns AlertSpec[] (dedupe keys make them safe
to run daily). All reads are tenant-scoped."""
from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal

from app import db
from app.modules.budgets import service as budget_service
from app.modules.goals import service as goal_service
from app.notifications.dispatch import AlertSpec

_MILESTONES = (25, 50, 75, 100)
_EXCL_TRANSFERS = "COALESCE(t.category, '') <> ALL(ARRAY['TRANSFER','TRANSFER_IN','TRANSFER_OUT','LOAN_PAYMENTS'])"


async def check_budgets(user_id: str, tenant_id: str) -> list[AlertSpec]:
    statuses = await budget_service.list_status(user_id, tenant_id)
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    month = today.strftime("%Y-%m")
    specs: list[AlertSpec] = []
    for b in statuses:
        if not b["is_active"]:
            continue
        cat, pct, limit, spent = b["category"], b["pct_used"], b["monthly_limit"], b["spent"]
        if pct >= 100:
            specs.append(AlertSpec("budget_threshold", f"{cat} budget exceeded",
                                   f"You've spent ${spent} of your ${limit} {cat} budget this month.",
                                   "warning", f"budget_over:{cat}:{month}"))
        elif pct >= b["alert_at_pct"]:
            left = days_in_month - today.day
            specs.append(AlertSpec("budget_threshold", f"{cat} budget at {pct}%",
                                   f"You've used {pct}% of your {cat} budget with {left} days left.",
                                   "info", f"budget_thresh:{cat}:{month}"))
        else:
            projected = (pct / today.day * days_in_month) if today.day > 0 else pct
            if projected > 110:
                specs.append(AlertSpec("budget_overpace", f"{cat} budget pacing high",
                                       f"At your current pace you'll use about {round(projected)}% of your "
                                       f"{cat} budget this month.", "info", f"budget_pace:{cat}:{month}"))
    return specs


async def check_goals(user_id: str, tenant_id: str) -> list[AlertSpec]:
    goals = await goal_service.list_goals(user_id, tenant_id)
    month = date.today().strftime("%Y-%m")
    specs: list[AlertSpec] = []
    for g in goals:
        if g["status"] != "active":
            continue
        gid, title, progress = g["goal_id"], g["title"], g["progress_pct"]
        for m in _MILESTONES:
            if progress >= m and await _record_milestone(tenant_id, gid, m):
                specs.append(AlertSpec("goal_milestone", f"Milestone reached: {title}",
                                       f"You've hit {m}% of your '{title}' goal. Keep it up!",
                                       "info", f"goal_ms:{gid}:{m}"))
        if not g["on_track"] and progress < 100:
            specs.append(AlertSpec("goal_behind", f"'{title}' is behind schedule",
                                   f"You're tracking behind on '{title}'. A small bump to your monthly "
                                   f"contribution can get you back on track.", "warning",
                                   f"goal_behind:{gid}:{month}"))
    return specs


async def _record_milestone(tenant_id: str, goal_id: str, pct: int) -> bool:
    """Record a milestone once (the table row IS the dedup). True if newly hit."""
    async with db.with_tenant(tenant_id) as conn:
        if await conn.fetchval(
            "SELECT 1 FROM goal_milestones WHERE goal_id = $1 AND milestone_pct = $2", goal_id, pct
        ):
            return False
        await conn.execute(
            """INSERT INTO goal_milestones (goal_id, tenant_id, milestone_pct, achieved_at, notified)
               VALUES ($1,$2,$3,NOW(),true)""",
            goal_id, tenant_id, pct,
        )
        return True


async def check_unusual_transactions(user_id: str, tenant_id: str) -> list[AlertSpec]:
    async with db.with_tenant(tenant_id) as conn:
        avg = await conn.fetchval(
            f"""SELECT AVG(t.amount)
                  FROM transactions t
                  JOIN plaid_accounts pa ON t.account_id = pa.account_id
                  JOIN plaid_items pi ON pa.item_id = pi.item_id
                 WHERE pi.user_id = $1 AND t.amount > 0 AND t.pending = false AND {_EXCL_TRANSFERS}
                   AND t.date >= CURRENT_DATE - INTERVAL '90 days'""",
            user_id,
        )
        if not avg:
            return []
        threshold = max(Decimal(avg) * 3, Decimal("200"))
        rows = await conn.fetch(
            f"""SELECT t.plaid_transaction_id AS id, t.amount, t.merchant_name
                  FROM transactions t
                  JOIN plaid_accounts pa ON t.account_id = pa.account_id
                  JOIN plaid_items pi ON pa.item_id = pi.item_id
                 WHERE pi.user_id = $1 AND t.amount > $2 AND t.pending = false AND {_EXCL_TRANSFERS}
                   AND t.date >= CURRENT_DATE - INTERVAL '2 days'
                 ORDER BY t.amount DESC LIMIT 10""",
            user_id, threshold,
        )
    return [
        AlertSpec("unusual_transaction", "Unusual large transaction",
                  f"A ${r['amount']} charge at {r['merchant_name'] or 'a merchant'} is well above your usual spending.",
                  "warning", f"unusual_tx:{r['id']}")
        for r in rows
    ]
