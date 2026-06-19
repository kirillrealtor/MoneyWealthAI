"""Transactions listing — tenant + user scoped (RLS). Static SQL with optional
filters bound as parameters (no string-built WHERE)."""
from __future__ import annotations

from typing import Any

from app import db

_SQL = """
    SELECT t.transaction_id, t.date, t.merchant_name, t.amount, t.category,
           t.pending, t.iso_currency_code
      FROM transactions t
      JOIN plaid_accounts pa ON t.account_id = pa.account_id
      JOIN plaid_items pi ON pa.item_id = pi.item_id
     WHERE pi.user_id = $1
       AND ($2::text IS NULL OR t.category = $2)
       AND ($3::text IS NULL OR t.merchant_name ILIKE $3)
       AND t.is_duplicate = false
     ORDER BY t.date DESC, t.transaction_id
     LIMIT $4 OFFSET $5
"""


async def list_transactions(
    user_id: str, tenant_id: str, *, limit: int, offset: int,
    category: str | None, search: str | None,
) -> list[dict[str, Any]]:
    like = f"%{search}%" if search else None
    async with db.with_tenant(tenant_id, user_id) as conn:
        rows = await conn.fetch(_SQL, user_id, category, like, limit, offset)
    return [
        {
            "transaction_id": str(r["transaction_id"]),
            "date": r["date"],
            "merchant_name": r["merchant_name"],
            "amount": r["amount"],
            "category": r["category"],
            "pending": r["pending"],
            "currency_code": r["iso_currency_code"],
        }
        for r in rows
    ]
