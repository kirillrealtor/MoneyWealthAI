# Phase 6 (Production Hardening) — Built vs. Deferred

Phase 6 is mostly **infrastructure**. The application-layer reliability and
observability are built and verified; the AWS provisioning is documented as the
deploy/DR playbook and is the remaining work.

## Scale/crash audit — fixed in-app ✅
A senior-audit pass for 1M-user crash/scale bugs. Request-serving hot path is
sound (no DB connection held across the LLM/Plaid network calls, all big-table
reads bounded by `LIMIT`/aggregate, `command_timeout=10` caps runaway queries,
background syncs semaphore-bounded). Three findings fixed:
- **Bounded connection acquisition** (`app/db.py`) — `pool.acquire()` now waits at
  most `_POOL_ACQUIRE_TIMEOUT` (5s) via a shared `_acquire()` used by every query
  path + `with_tenant`. On pool exhaustion it raises a clean **`503 SERVICE_BUSY`**
  (load shed, LB-retryable) instead of blocking indefinitely → request pile-up →
  OOM. This was the most likely crash-under-load mode.
- **Plaid `list_items` N+1 → single `LEFT JOIN`** (`app/modules/plaid/service.py`)
  — one round-trip regardless of item count; grouped in-app.
- **JWT verified once per request** (`app/deps.py`) — claims memoized on
  `request.state`; the rate limiter and `require_auth` no longer each re-verify the
  signature.

The remaining 1M-scale item is **not a code bug** — it's the alert-runner SQS
fan-out (see below): `scripts/run_alerts.py` is O(users) sequential and must move
to a worker fleet to complete inside a daily window at scale.

## Built & verified (in-app) ✅
- **AI provider auto-fallback** — `FallbackProvider` fails Claude→Groq on error
  (Tier-2 degradation), recording each attempt. Verified by unit test.
- **AI degradation tier** — Redis error-rate window → `/health/ai` (0/1/2).
- **`/metrics`** — Prometheus exposition: `ai_calls_total{provider}`,
  `ai_errors_total{provider}`, `ai_tokens_total`, `ai_validation_failures_total`,
  `ai_degradation_tier`. Verified live + integration test.
- **Partition cron** — `python -m scripts.ensure_partitions` (idempotent; creates
  current + next 3 months). Verified.
- **Load test** — `tests/load/advisor_load_test.js` (k6) with the p95/error thresholds.
- **Docs** — `PRODUCTION_DEPLOYMENT.md`, `DR_RUNBOOK.md`.

## Deferred — infrastructure-as-code (the real remaining work)
- 🏗️ **Terraform/IaC** for: Aurora Serverless v2 (Multi-AZ), **RDS Proxy**, ElastiCache
  Redis (Multi-AZ), ECS Fargate (API + worker services, autoscaling), ALB, **WAF**,
  **Secrets Manager** + rotation Lambda, **SQS** queues + DLQs, EventBridge schedules,
  S3, CloudWatch alarms/dashboards.
- 🏗️ **SQS consumers** — wire the existing idempotent units (`run_sync_for_item`,
  `run_alerts_for_user`, notification dispatcher, outbox retry) to SQS workers, replacing
  the in-process spawn / cron loops. Transport swap, not a rewrite.
- 🏗️ **EventBridge schedules** — daily alert scan, weekly digest, monthly partitions,
  90-day secret rotation.
- 🏗️ **Outbox retry worker** — re-attempt `notification_outbox` `status='failed'` with
  backoff (table + `idx_outbox_pending` exist).
- 🧩 **Perf** — cache the per-advisor-turn snapshot; prompt-cache the static system-prompt
  prefix (the live snapshot currently busts the cache) to cut input-token cost at volume.
- ⚙️ **SOC 2** prep — audit_logs + access logging are in place; formal audit at Series A.

## What to provision first (smallest path to a safe prod)
1. Aurora Multi-AZ + **RDS Proxy** + Secrets Manager → `DATABASE_URL` as `app_user`.
2. ElastiCache Redis (Multi-AZ). 3. ECS API behind ALB + **WAF** + TLS.
4. SQS + worker service for Plaid sync & alerts. 5. EventBridge schedules.
6. Prometheus scrape of `/metrics` + the alarms in `PRODUCTION_DEPLOYMENT.md`.
