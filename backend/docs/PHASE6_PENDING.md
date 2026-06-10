# Phase 6 (Production Hardening) — Built vs. Deferred

Phase 6 is mostly **infrastructure**. The application-layer reliability and
observability are built and verified; the AWS provisioning is documented as the
deploy/DR playbook and is the remaining work.

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
