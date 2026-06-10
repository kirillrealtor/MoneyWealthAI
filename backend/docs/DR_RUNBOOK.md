# Disaster Recovery Runbook (Phase 6)

A finance product has a higher DR bar than typical SaaS — users make money
decisions on what they see. This is the recovery playbook. Drill it on staging.

## RTO / RPO targets

| System | Scenario | RTO | RPO |
|---|---|---|---|
| Aurora | instance failure | 30s (auto-failover) | 0 |
| Aurora | accidental delete / bad write | 2–4h (PITR) | ≤5 min |
| ECS API | deploy failure | 10 min (rollback) | n/a |
| AI provider | outage | <2 min (auto-fallback) | n/a |
| Plaid | outage | serve cached data | 24h |
| Redis | cache loss | minutes (rebuilds) | n/a (ephemeral) |

## Scenario A — Aurora instance failure
Multi-AZ handles it automatically (~30s). The app pool reconnects on next query.
**Action:** confirm the CloudWatch failover alarm cleared; `SELECT 1` smoke test.

## Scenario B — accidental data deletion / corrupt write
1. **Freeze writes**: set the cluster parameter `default_transaction_read_only=on`
   (or enable deletion protection) to stop further damage.
2. **Identify T** (incident time) from CloudWatch / audit_logs.
3. **PITR restore to a NEW cluster** at `T − 5min` (`restore-db-cluster-to-point-in-time`).
   Do **not** overwrite the live cluster.
4. **Validate** row counts on the restored cluster (`users`, `transactions`, `budgets`…).
5. **Swing traffic**: update `DATABASE_URL` in Secrets Manager to the restored cluster's
   RDS Proxy; redeploy; `curl /health/ready`.
6. **Replay the gap**: re-run Plaid sync (Plaid retains data — re-sync is idempotent);
   replay user-created writes from `audit_logs` if needed.

## Scenario C — AI provider outage
✅ **Automatic**: `FallbackProvider` fails Claude→Groq; `ai_degradation_tier` reflects it
at `/health/ai` and `/metrics`. If **all** providers are down, advisor endpoints return a
clean `503` (`AI_UNAVAILABLE`) — **every non-AI feature keeps working** (dashboards,
budgets, goals, notifications). No data is lost; alerts queue and send on recovery.
**Action:** monitor the tier; page if `=2` persists.

## Scenario D — Redis loss
Cache is ephemeral. Rate limiting and notification dedup **fail open** (documented),
so the app keeps serving. Spin up a fresh ElastiCache node; counters rebuild.
**Risk to watch:** with Redis down there's no rate limiting → pair with the WAF rate
rules and a hard provider-side spend cap so an outage can't run up AI cost.

## Scenario E — bad deploy
`ECS` blue/green → **rollback to previous task definition** (10 min). CI's eval gate +
smoke test should catch most regressions pre-promote.

## Drills (run on staging)
| Drill | Frequency | Pass criteria |
|---|---|---|
| Aurora failover | monthly | recovers <60s, 0 data loss |
| PITR restore | quarterly | restore <30m, row counts match |
| AI fallback | monthly | force Claude error → Groq serves, tier reflects it |
| Redis flush | quarterly | app keeps serving, no 5xx |
| Full blackout | bi-annual | Tier-2 banner, dashboards load, no corruption |
