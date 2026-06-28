# Backend Build Sequence

You chose the full blueprint. This is the order to build it so there's always something working end-to-end. Each phase is shippable and testable before the next starts. Do **not** build horizontally (all schema, then all services); build **vertical slices**.

## Phase 0 — Foundation (Week 1)
- Repo, TypeScript, Fastify, Docker, lint/type-check/test CI (Section 23).
- Aurora (Serverless v2) + **RDS Proxy** + Redis + Secrets Manager — **provisioned** in `infra/terraform/`.
- Run `db/schema.sql` migration. Migration tooling (e.g. node-pg-migrate / Drizzle).
- Health endpoint, structured logger (Section 19.1), trace_id middleware.
- **Exit test:** container boots, connects through RDS Proxy, `/health` green.

## Phase 1 — Auth + Tenancy skeleton (Week 1–2)
- Signup, email verify, login, JWT + refresh rotation, sessions table.
- Tenant resolution middleware + RLS context (`app.current_tenant_id`).
- Rate limiting (Redis). Zod on every route. audit_logs writing.
- **Exit test:** a user can register under the retail tenant and authenticate.

## Phase 2 — Plaid vertical slice (Week 2–3) ← highest risk, do early
- link-token → exchange → **KMS-encrypt** access token → store.
- Idempotent `transactions/sync` worker (cursor + `ON CONFLICT`), sync_jobs.
- Plaid webhook receiver → SQS → sync worker.
- Soft-duplicate cleanup job. Investments + liabilities sync.
- **Exit test:** connect a real bank (production), 24mo history lands, re-running sync produces zero dupes.

## Phase 3 — AI core (Week 3–5) ← the differentiator
- `callAdvisorLLM` interface (Claude only to start, fallback stubs behind it).
- MCP tools (start with `get_spending_summary`, `get_account_balances`, `get_cash_flow`), each with **tool-result-limiter**.
- Agentic loop, system prompt assembly, persona config.
- **Output validator** (grounding, compliance, SQL/key leak) + retry-once.
- Input safety: prompt-injection / jailbreak / crisis detection.
- Token budgeting per tier. Conversation summarization past ~15K tokens.
- Evals harness (Section 18) + golden set ≥ 50 cases, CI gate ≥ 90%.
- **Exit test:** evals green; a real question returns a grounded, compliant answer with visible tool calls.

## Phase 4 — Planning modules (Week 5–6)
- Budget CRUD + categorization. Goals + reverse-engineering math (unit tested, Section 22.1). Debt snowball/avalanche + DTI. Portfolio allocation/concentration.
- Remaining MCP tools wired to these.

## Phase 5 — Proactive layer (Week 6–7)
- Alert engine (EventBridge daily). Notification router (channels, dedup, prefs, TCPA opt-out). Weekly digest.

## Phase 6 — Production hardening (Week 7–9)
- Observability: AI metrics dashboard, CloudWatch alarms, SLOs (Section 19).
- DR: PITR runbook tested on staging, failover drill, LLM-fallback drill (Section 17).
- WAF, secrets rotation, load test to 200 concurrent (Section 22.3).
- transactions partition-creation cron (1 month ahead).

## Phase 7 — Deferred-but-committed (post-launch, as blueprint)
- Add GPT-4o/Gemini to the fallback chain (interface already there).
- White-label partner dashboard + per-tenant API keys/metering (schema already there).
- i18n / multi-currency / RTL. A/B framework. SOC 2 formal audit.

---

## Critical-path risks to watch
1. **Plaid production approval** — apply *now*; it gates Phase 2 and has lead time.
2. **AI cost at 100K** — the tool-result-limiter + token budgets are what keep this from being ruinous. Build them in Phase 3, not later.
3. **Compliance framing** — zero-tolerance validator must exist before any AI ships to a real user.
4. **Connection exhaustion** — RDS Proxy is Phase 0, not an optimization.
