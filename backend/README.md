# AI Financial Advisor — Backend

Python / FastAPI backend (async). Aurora-compatible Postgres (asyncpg) + Redis.
Built per [docs/BACKEND_ARCHITECTURE.md](docs/BACKEND_ARCHITECTURE.md) on the
build order in [docs/BUILD_SEQUENCE.md](docs/BUILD_SEQUENCE.md).

> **Stack note:** Backend is Python (FastAPI). Frontend is TypeScript (Next.js).
> Python is the primary application language; if/when heavy quant or ML work
> appears (evals, Monte Carlo modeling, embeddings), it stays in Python too.

## Status
- ✅ **Phase 0** — scaffold, config, asyncpg pool (RDS-Proxy-ready), SQL migrations, structlog, tracing, health
- ✅ **Phase 1** — auth (signup, email verify, login, JWT + rotating refresh, sessions), tenancy, rate limiting, audit log
- ✅ **Phase 1 hardening** — enforced RLS (non-owner role + FORCE RLS), brute-force throttle, anti-enumeration, bcrypt pre-hash, security headers, trusted-host, body limits, captcha, integration + RLS tests. See [docs/SECURITY.md](docs/SECURITY.md).
- ✅ **Phase 2** — Plaid data layer: link/exchange/disconnect, **encrypted access tokens (AES-256-GCM)**, idempotent transaction sync, **verified webhooks**, tenant RLS on all Plaid tables. Live calls need Plaid keys — see [docs/PHASE2_PENDING.md](docs/PHASE2_PENDING.md).
- ✅ **Phase 3** — AI advisor core: grounded **agentic loop** (Claude **or** Groq) + MCP tools (tenant-scoped, **FORCE RLS**), input safety (injection/crisis/jailbreak), output validation, **atomic** per-tier token budgets, **evals harness** (`python -m scripts.run_evals`). Live calls need `ANTHROPIC_API_KEY` or `GROQ_API_KEY` — see [docs/PHASE3_PENDING.md](docs/PHASE3_PENDING.md).
- ✅ **Phase 4** — planning: **Decimal-exact calculation engine** (debt snowball/avalanche, goal reverse-engineering, affordability) + **Budgets** and **Goals** modules (CRUD, tenant RLS) + 6 new MCP tools (budget/goals/debt/portfolio/affordability/debt-payoff) wired into the advisor.
- ✅ **Phase 4B** — Debt dashboard (summary, DTI, payoff-at-minimum, refinance flags, snowball/avalanche what-if) + Portfolio dashboard (allocation, sector exposure, concentration flags, unrealized P/L, rebalance gaps) — tenant RLS, data-only (no buy/sell directives).
- ⏭️ **Phase 5** — alert engine, notifications, weekly digest

## Quick start (local)

This package lives at `backend/` in the monorepo. `docker-compose.yml` is at the
**repo root** (one level up); run app commands from this `backend/` directory.

```bash
# from the repo root: start datastores (Postgres :5433, Redis :6380)
docker compose up -d postgres redis

# from backend/
cp .env.example .env
python -m venv .venv && source .venv/bin/activate   # (Windows: .venv\Scripts\activate)
pip install -r requirements-dev.txt
python -m scripts.migrate                      # apply db/migrations/*.sql
uvicorn app.main:app --reload --port 3000      # http://localhost:3000
```

Or run everything in containers from the repo root: `docker compose up --build`.

## Verify it's up
```bash
curl localhost:3000/health
curl localhost:3000/health/ready

# Auth flow
curl -X POST localhost:3000/api/v1/auth/signup \
  -H 'content-type: application/json' \
  -d '{"email":"me@example.com","password":"SecurePass123!"}'
# -> check server logs for the dev verification link (MAIL_TRANSPORT=console)

curl -X POST localhost:3000/api/v1/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"me@example.com","password":"SecurePass123!"}' -c cookies.txt
# -> { access_token, user_id }; refresh token set as httpOnly cookie

curl localhost:3000/api/v1/auth/me -H "authorization: Bearer <access_token>"
```

Interactive API docs: http://localhost:3000/docs (FastAPI auto-generated).

## Commands
| Command | Purpose |
|---|---|
| `uvicorn app.main:app --reload` | Hot-reload dev server |
| `python -m scripts.migrate` | Apply pending SQL migrations |
| `ruff check .` | Lint |
| `mypy app scripts` | Type-check |
| `pytest` | Unit tests |

## Layout
```
app/
  config.py            env validation (pydantic-settings)
  main.py              FastAPI factory + lifespan
  middleware.py        ASGI tracing + access log
  context.py           contextvars trace_id
  db.py                asyncpg pool, query helpers, with_tenant (RLS)
  redis_client.py  logging_conf.py  crypto.py  errors.py  audit.py
  deps.py              require_auth, resolve_tenant, rate_limit
  modules/
    auth/              tokens, mailer, schemas, service, router
    health/
db/
  migrations/          executable schema (source of truth)
  schema.sql           annotated reference
scripts/migrate.py     migration runner
```

## Security notes (Phase 1)
- Passwords: bcrypt (rounds configurable, default 12).
- Refresh tokens: opaque, only SHA-256 hash stored; rotated on every refresh; reuse rejected.
- Access tokens: short-lived JWT (HS256), held in memory by clients.
- Tenant isolation: `X-Tenant-ID` resolution + Postgres RLS via `with_tenant()`.
- PII never logged; structured logs redact sensitive keys.
