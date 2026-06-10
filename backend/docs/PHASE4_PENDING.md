# Phase 4 (A + B) — Deferred Items & TODOs

Phases 4A (Budgets, Goals, calculation engine, planning MCP tools) and 4B (Debt +
Portfolio dashboards) are built, tenant-isolated, and tested. This is the honest
list of what's **not** done — verified against the code.

Legend: 🔴 blocks real value · 🟠 completeness gap · 🟡 nice-to-have · ✅ deliberate boundary
Each item: 🧩 small code · ⚙️ config/infra · ⏭️ belongs to another phase

---

## In-scope gaps (small, finish to "complete" 4A/B)

- 🟠 🧩 **Goal milestones not wired.** `goal_milestones` table exists but no code uses it —
  the 25/50/75/100% milestone tracking + celebration from the blueprint is unimplemented.
- 🟠 🧩 **Budget category ↔ transaction category mismatch.** `budget.category` is free text
  (no validation); spend is matched against Plaid's normalized `transaction.category`. If a
  user types "Dining" but Plaid labels it "FOOD_AND_DRINK", **spend won't map → budget shows
  $0 spent**. Needs a shared category vocabulary + a category picker/validation.
- 🟠 🧩 **Goal `current_amount` is manual.** The blueprint's "auto-link a savings account to
  track progress" isn't built; users update progress by hand.
- 🟡 🧩 **Cash-flow forecast / end-of-month projection** (`forecast_end_of_month`) — not built
  as a tool or endpoint.
- 🟡 🧩 **Recurring-subscription detector** (Module 2 budget feature) — not built.
- 🟡 🧩 **Debt refinance detector is simplified** — flags `above_typical_rate` against fixed
  thresholds; the "compare to live market rates" version isn't there.

## Cross-phase dependencies (block full 4B value, but aren't 4B code)

- 🔴 ⏭️ **No data source for the debt/portfolio dashboards.** `debt_accounts` and
  `portfolio_holdings` have **no writer** — the Plaid **liabilities/investments sync** is
  deferred (Phase 2 follow-up). Until it ships, both dashboards return empty in production.
  See `docs/PHASE2_PENDING.md` — includes the **APR-normalization landmine** (Plaid returns
  APR as a percentage `24.99`; the engine expects a fraction `0.2499` — a mismatch is 100× wrong).
- 🟠 ⏭️ **Budget `alert_at_pct` is stored but never fires.** CRUD only; the actual
  pacing/threshold alerting belongs to the **Phase 5 alert engine**. The field is dead until then.
- ⏭️ **Goal-behind-schedule + budget-overpace alerts** → **Phase 5** (alerts + notifications).

## Deliberate boundaries (NOT TODOs — flagged so they aren't mistaken for gaps)

- ✅ **Portfolio rebalancing returns allocation _gaps_, not buy/sell instructions.** Intentional,
  to stay on the educational side of SEC/RIA rules. Turning these into trade recommendations
  needs legal/RIA sign-off, not just code.
- ✅ **All AI/dashboard outputs are "educational, not advice"** — enforced in the system prompt
  and the output validator.

---

## Priority if resuming Phase 4
1. **#8 Liabilities/investments sync** (Phase 2 follow-up) — without it the debt/portfolio
   dashboards are empty. Highest-value.
2. **#2 Budget category mapping** — without it budgets can silently show $0 spent.
3. Then #1 (milestones), #4 (goal auto-link), #6 (forecast).

The rest naturally fold into Phase 5 (alerts/notifications).
