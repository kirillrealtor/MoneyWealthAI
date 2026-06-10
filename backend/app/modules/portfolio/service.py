"""Portfolio dashboard logic — tenant-scoped reads over Plaid-synced holdings.
Data-only: allocation, exposure, concentration risk, rebalance gaps. No advice."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from app import db

_SECTOR_CONCENTRATION = 30.0  # % of portfolio in one sector -> flag
_HOLDING_CONCENTRATION = 20.0  # % of portfolio in one holding -> flag
_MAX_HOLDINGS = 500  # bound the result set (memory / DoS guard at scale)


async def _fetch_holdings(conn: Any, user_id: str) -> list[Any]:
    return list(await conn.fetch(
        f"""SELECT ph.name, ph.ticker, ph.asset_class, ph.sector,
                   ph.institution_value, ph.cost_basis
              FROM portfolio_holdings ph
              JOIN plaid_accounts pa ON ph.account_id = pa.account_id
              JOIN plaid_items pi ON pa.item_id = pi.item_id
             WHERE pi.user_id = $1
             ORDER BY ph.institution_value DESC NULLS LAST LIMIT {_MAX_HOLDINGS}""",
        user_id,
    ))


def _pct(part: Decimal, whole: Decimal) -> float:
    return round(float(part / whole * 100), 1) if whole > 0 else 0.0


async def get_summary(user_id: str, tenant_id: str) -> dict[str, Any]:
    async with db.with_tenant(tenant_id) as conn:
        rows = await _fetch_holdings(conn, user_id)

    total = sum((r["institution_value"] or Decimal("0")) for r in rows)
    total = Decimal(total)
    unrealized = sum(((r["institution_value"] or Decimal("0")) - (r["cost_basis"] or Decimal("0"))) for r in rows)

    by_class: dict[str, Decimal] = {}
    by_sector: dict[str, Decimal] = {}
    holdings: list[dict[str, Any]] = []
    for r in rows:
        val = r["institution_value"] or Decimal("0")
        cls = r["asset_class"] or "unknown"
        sec = r["sector"] or "unknown"
        by_class[cls] = by_class.get(cls, Decimal("0")) + val
        by_sector[sec] = by_sector.get(sec, Decimal("0")) + val
        holdings.append({
            "name": r["name"], "ticker": r["ticker"], "asset_class": r["asset_class"],
            "sector": r["sector"], "value": r["institution_value"],
            "unrealized_gain_loss": ((r["institution_value"] or Decimal("0")) - (r["cost_basis"] or Decimal("0"))),
        })

    flags: list[str] = []
    for sec, val in by_sector.items():
        p = _pct(val, total)
        if sec != "unknown" and p >= _SECTOR_CONCENTRATION:
            flags.append(f"{p}% of your portfolio is in {sec}.")
    for h in holdings:
        p = _pct(h["value"] or Decimal("0"), total)
        if p >= _HOLDING_CONCENTRATION and h["ticker"]:
            flags.append(f"{p}% of your portfolio is a single holding ({h['ticker']}).")

    holdings.sort(key=lambda h: h["value"] or Decimal("0"), reverse=True)
    return {
        "total_value": total.quantize(Decimal("0.01")),
        "unrealized_gain_loss": Decimal(unrealized).quantize(Decimal("0.01")),
        "allocation_pct": {k: _pct(v, total) for k, v in by_class.items()},
        "sector_exposure_pct": {k: _pct(v, total) for k, v in by_sector.items()},
        "concentration_flags": flags,
        "top_holdings": holdings[:10],
        "note": None if rows else "No investment holdings linked.",
    }


async def rebalance_gaps(user_id: str, tenant_id: str, target: dict[str, float]) -> dict[str, Any]:
    async with db.with_tenant(tenant_id) as conn:
        rows = await _fetch_holdings(conn, user_id)
    total = Decimal(sum((r["institution_value"] or Decimal("0")) for r in rows))
    if total <= 0:
        return {"total_value": Decimal("0.00"), "gaps": [], "note": "No investment holdings linked."}

    by_class: dict[str, Decimal] = {}
    for r in rows:
        cls = r["asset_class"] or "unknown"
        by_class[cls] = by_class.get(cls, Decimal("0")) + (r["institution_value"] or Decimal("0"))

    gaps = []
    for cls in sorted(set(by_class) | set(target)):
        current_val = by_class.get(cls, Decimal("0"))
        current_pct = _pct(current_val, total)
        target_pct = float(target.get(cls, 0.0))
        target_val = (total * Decimal(str(target_pct)) / Decimal("100")).quantize(Decimal("0.01"))
        gaps.append({
            "asset_class": cls, "current_pct": current_pct, "target_pct": target_pct,
            "drift_pct": round(current_pct - target_pct, 1),
            "current_value": current_val.quantize(Decimal("0.01")), "target_value": target_val,
            "adjustment_value": (target_val - current_val).quantize(Decimal("0.01")),
        })
    return {"total_value": total.quantize(Decimal("0.01")), "gaps": gaps,
            "note": "Educational rebalancing analysis — not investment advice."}
