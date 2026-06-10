# Phase 5 (Proactive Layer) — Built & Deferred

Built: tenant-isolated, idempotent **alert engine** + **in-app notifications** +
**preference center**, with a **batched runner** that's SQS-ready. Works with
**zero external accounts**.

Legend: 🔑 key/account · ⚙️ config/infra · 🧩 small code

## Built & verified (no action needed)
- **Alert checks**: budget threshold/overpace, goal-behind, goal-milestone (wires the
  `goal_milestones` table), unusual-large-transaction. Plaid webhook now raises
  bank-connection-error / token-expiring alerts.
- **Dispatcher**: Redis dedup (24h) + `notification_outbox` `UNIQUE(dedupe_key, channel)`
  → at-least-once, never double-notify. Honors per-type toggles, channel opt-ins, **TCPA
  SMS opt-in**, and **quiet hours** (tz-aware, fail-safe).
- **In-app notifications** = `alerts` rows. API: `GET /notifications`, `POST /{id}/read`,
  `POST /read-all`, `GET|PATCH /notifications/preferences`.
- **Tenant isolation**: `FORCE RLS` on `alerts`, `notification_preferences`,
  `notification_outbox`; cross-tenant scan via a `SECURITY DEFINER` keyset pager
  (`list_users_for_scan`) — no RLS bypass for the app role.
- **Runner**: `python -m scripts.run_alerts` (cron-triggerable; per-user unit of work).

## To activate channels (gated, like email/captcha)
- 🔑🧩 **Email** notifications already deliver via the pluggable `send_mail()` (console in
  dev). Wire SES/Postmark to send for real (same adapter as auth email).
- 🔑🧩 **Push (FCM)** — `channels.is_configured("push")` returns False; implement the FCM
  adapter + device-token storage, then flip it on.
- 🔑🧩 **SMS (Twilio)** — gated behind `sms_opt_in` (TCPA); implement the Twilio adapter.
- ⚙️ One-click email **unsubscribe** (signed token) for CAN-SPAM before sending marketing/digest.

## Deferred to Phase 6 (infra) / later
- ⚙️ **Scheduler + SQS fan-out** — `run_alerts` is a cron loop today; production fans
  per-user/batch work to an **SQS worker fleet** (EventBridge schedule). `run_alerts_for_user`
  is already the unit of work, so it's a transport swap, not a rewrite.
- ⚙️ **Outbox retry worker** — a worker that re-attempts `status='failed'` rows with backoff
  (the table + index `idx_outbox_pending` are in place).
- 🧩 **Weekly digest** (`scripts/run_digest`) — Sunday email: net worth, spend, goal progress,
  + a short AI narrative (cheap model / Batches API at scale). Honors `weekly_digest` pref.
- 🧩 **Unusual-transaction detector** could use stddev (z-score) instead of the 3× / $200
  heuristic for fewer false positives.
