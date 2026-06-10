# Production Deployment & Ops (Phase 6) — 1M-user target

The application is built to be **config-driven** — going to production is mostly
provisioning AWS and pointing env vars at it, not code changes. This is the
deploy/ops playbook. Items marked 🏗️ are infrastructure-as-code (Terraform) to
provision; ✅ are already done in the app.

## Topology

```
            Route53 + ACM (TLS 1.3)
                   │
            AWS WAF  (rate/bot rules, OWASP)
                   │
        ALB ──► ECS Fargate (API, N replicas, autoscaled on CPU/RPS)
                   │                         │
            RDS Proxy ──► Aurora PG          ElastiCache Redis (Multi-AZ)
            (Serverless v2, Multi-AZ)
                   │
        SQS ──► ECS Fargate (worker fleet: Plaid sync, alerts, digest, outbox retry)
                   │
   EventBridge (cron: daily alerts, weekly digest, monthly partitions, secret rotation)
                   │
        S3 (statements, audit archives 7y)   Secrets Manager   CloudWatch
```

## Data layer
- 🏗️ **Aurora PostgreSQL Serverless v2** (0.5–16 ACU autoscale), **Multi-AZ** (≈30s failover).
- 🏗️ **RDS Proxy** in front — **non-negotiable**. The app pool is sized per-instance
  (`max_size=10`); RDS Proxy multiplexes the fleet onto a small set of real Aurora
  connections. Point `DATABASE_URL` at the **proxy** endpoint, as **`app_user`** (non-owner,
  `NOBYPASSRLS`). `MIGRATION_DATABASE_URL` → owner, used only during deploys.
- ✅ **RLS everywhere** (FORCE) — the app is already non-owner + tenant-scoped.
- ✅ **Partitioned `transactions`** — schedule `python -m scripts.ensure_partitions` monthly
  (EventBridge) so new months never fall into the default partition.
- 🏗️ **PITR** enabled (35-day backups). See `DR_RUNBOOK.md`.

## Secrets — AWS Secrets Manager (never env files in prod)
`DATABASE_URL`, `MIGRATION_DATABASE_URL`, `REDIS_URL`, `JWT_ACCESS_SECRET`,
`JWT_REFRESH_SECRET`, `PLAID_*`, `PLAID_ENC_KEY` (KMS-backed), `ANTHROPIC_API_KEY`,
`GROQ_API_KEY`, `TURNSTILE_SECRET_KEY`, email/Twilio/FCM keys.
- 🏗️ Inject as env at container start; the config loader is unchanged.
- 🏗️ **Rotation Lambda** every 90 days (JWT secrets, DB password, provider keys).
  Note: rotating `JWT_*` invalidates active sessions — plan the window.

## Async workers — SQS (replaces in-process fire-and-forget)
- 🏗️ Queues + DLQs: `plaid-sync`, `alerts`, `notifications`, `digest`, `outbox-retry`.
- ✅ The per-unit functions already exist and are idempotent:
  `run_sync_for_item`, `run_alerts_for_user`, the notification dispatcher (Redis dedup +
  outbox UNIQUE). Swapping the in-process spawn / cron loop for SQS consumers is a
  **transport change, not a rewrite**.
- 🏗️ EventBridge schedules: daily alert scan (fan out via `list_users_for_scan`), weekly
  digest, monthly `ensure_partitions`.

## Edge & transport
- 🏗️ **AWS WAF** (managed rule sets + per-IP rate rules) — complements the app-layer
  throttle/captcha. ✅ App already sets security headers, HSTS (prod), TrustedHost, body limits.
- 🏗️ TLS 1.3 at ALB; ensure the LB doesn't strip the app's HSTS.
- ✅ CORS allowlist via `CORS_ORIGINS`; set real frontend origin. Set real `ALLOWED_HOSTS`.

## Observability
- ✅ **`/metrics`** (Prometheus) — AI calls/errors/tokens/validation-failures + degradation tier.
  ✅ **`/health/ai`** (tier), ✅ `/health/ready` (DB+Redis). ✅ Structured logs with trace_id,
  PII-redacted.
- 🏗️ Scrape `/metrics` (ADOT/Prometheus → CloudWatch/Grafana). Wire the alarms below.

| Alarm | Warn | Critical | Action |
|---|---|---|---|
| `ai_degradation_tier` | ≥1 | =2 | auto-fallback already on; page on 2 |
| `ai_errors_total` rate | >5%/5m | >20%/2m | provider incident |
| `ai_validation_failures_total` rate | >2% | >5% | freeze prompt deploys |
| daily AI token spend | > $200 | > $500 | review usage / cap |
| Aurora CPU / ACU | >70% | >90% | scale ceiling |
| SQS DLQ depth | >0 | growing | failed jobs to investigate |
| p95 dashboard | >500ms | >1s | DB/cache |

## Performance to hit at 1M (targets + levers)
- Dashboard p95 < 500ms (Aurora reader endpoint + Redis cache), AI p95 < 8s (streaming),
  API p99 < 500ms (RDS Proxy pooling). Load test with `tests/load/advisor_load_test.js`.
- ✅ Bounded tool results + per-tier token budgets keep AI cost survivable.
- 🧩 **Cache the per-advisor-turn snapshot** and **prompt-cache** the static system-prompt
  prefix to cut input-token cost at volume (the live snapshot currently busts the cache).
- ✅ Provider **auto-fallback** (Claude→Groq) for AI availability.

## Deploy pipeline
- ✅ CI: lint, type-check, unit+integration tests, security scan, **AI eval gate** (≥90%).
- 🏗️ CD: build image → push ECR → `migrate` (as owner) → blue/green ECS deploy → smoke test.
- 🏗️ Migrations must be backward-compatible (old code runs against new schema); two-deploy
  pattern for breaking changes (add nullable → backfill → constrain).
