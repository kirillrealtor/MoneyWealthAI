# Security Posture — Phase 1

Status of the security controls implemented and verified in the auth/platform layer.

## Authentication
- **Passwords:** bcrypt (rounds=12), with **SHA-256 pre-hash** so passwords >72 bytes are not silently truncated.
- **Access tokens:** short-lived JWT (HS256, 15 min), held in memory by clients. **`iss`/`aud` claims** are set and verified — a token minted for another audience is rejected.
- **Refresh tokens:** opaque 48-byte secrets; only the SHA-256 hash is stored. **Rotated on every use**; replaying a rotated/revoked token is treated as theft and **revokes the entire session family** for that user (verified by test).
- **Login anti-enumeration:** a dummy bcrypt verification runs when the account doesn't exist, so success/failure take ~equal time.
- **Brute-force defense (no DoS vector):** the hard 429 lock (10 fails / 15 min) is keyed by **(tenant, email, IP)** so an attacker can't freeze a victim who logs in from another IP; the captcha step-up is keyed by (tenant, email) and only adds friction (never a lockout). Both fail **open** if Redis is down.
- **Captcha (Cloudflare Turnstile):** required on signup; **step-up** on login only after `LOGIN_CAPTCHA_AFTER_FAILS` (default 3) failures, so normal logins stay frictionless. Disabled by default (no-op) in dev/test; enabled via `TURNSTILE_ENABLED` + secret. Verification fails **closed** on Cloudflare/network error. Email provider for verification is pluggable behind `send_mail()` (console stub in dev; SES/Postmark TBD).

## Tenant Isolation (multi-tenant / white-label)
- App connects as a **non-owner `app_user` role** (`NOBYPASSRLS`); migrations run as the owner/superuser.
- `users` has **`FORCE ROW LEVEL SECURITY`** with a `USING` + `WITH CHECK` policy keyed on `app.current_tenant_id`.
- Every users-table access runs inside `db.with_tenant()`, which sets the tenant context transaction-locally.
- Secret-token tables (`user_sessions`, `email_verification_tokens`) carry `tenant_id` so token lookups resolve the tenant without a circular read of the RLS-protected `users` table.
- **Verified:** as `app_user`, `SELECT * FROM users` with no tenant context returns **0 rows** (fails closed). Integration tests assert this.

## Transport / HTTP hardening
- Security headers on every response: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy`, `Permissions-Policy`, `Cache-Control: no-store`, plus **HSTS in production**.
- **TrustedHostMiddleware** (anti Host-header injection) — allowlist via `ALLOWED_HOSTS`.
- **Body-size limit** — requests over `MAX_BODY_BYTES` (default 1 MB) rejected with 413 before buffering.
- **CORS** — credentialed, explicit origin allowlist via `CORS_ORIGINS` (empty = no cross-origin); methods/headers restricted.
- **Rate limiting** — Redis fixed-window, keyed by a stable SHA-256 bucket; keyed by **user id (`sub`)** when authenticated (not the rotating JWT string) so a limit isn't reset by token refresh; by client IP otherwise. Consistent across instances; fails open.

## Data / secrets
- Parameterized queries only (asyncpg `$1` params); no string interpolation.
- **Validation errors are scrubbed** — the raw `input` (which would echo a submitted password/PII) is stripped; only field location/type/message is returned. Request models use `extra="forbid"` to reject unexpected fields.
- Structured logs redact secrets (password, tokens, authorization, cookie) and never log email/phone at info level in prod.
- Standardized error envelope; no stack traces, DB internals, or third-party (Plaid) error details leak to clients.
- Production secrets come from AWS Secrets Manager (injected as env); never committed.

## Plaid data layer (Phase 2)
- **Access tokens encrypted at rest** — AES-256-GCM, random 96-bit nonce, versioned key, **AAD-bound to the owning user_id** (a token blob can't be transplanted to another row). Plaintext tokens are never logged or returned. Verified: tamper and wrong-AAD both fail decryption.
- **Webhook verification** — `Plaid-Verification` JWT must be **ES256**, signature checked against Plaid's JWK, **iat freshness < 5 min** (anti-replay), and **SHA-256(body)** constant-time-compared to the signed claim. Forged/unsigned webhooks rejected (401) before any action. Verified live.
- **Tenant isolation** — `tenant_id` + `FORCE ROW LEVEL SECURITY` on every Plaid table (`plaid_items/accounts`, `transactions`, `portfolio_holdings`, `debt_accounts`, `sync_jobs`). Verified: `app_user` reads 0 rows without tenant context. The one legitimate cross-tenant lookup (webhook → tenant) uses a single `SECURITY DEFINER` resolver, not an RLS-bypass grant.
- **Idempotent sync** — Plaid cursor + `ON CONFLICT (plaid_transaction_id, date)` + a Redis per-item lock; re-running never double-counts (unit-proven).
- **Access control** — link/exchange/disconnect require auth **and** verified email, rate-limited; disconnect revokes the item at Plaid then purges local data.

## AI advisor (Phase 3)
- **Tool data isolation (the key AI property):** MCP tool executors receive `user_id`/`tenant_id` from the authenticated request — **never** from the LLM — and run inside `with_tenant()`. The model cannot reach another user's or tenant's data even under prompt injection. LLM-supplied tool inputs are Pydantic-validated and only ever become SQL `$` params.
- **Prompt-injection sanitizer** + **jailbreak classifier** (cheap Haiku, gated to investment-adjacent messages, fails open) on every inbound message.
- **Crisis protocol**: financial-distress messages bypass the LLM entirely and return support resources (verified live).
- **Output validator** (defense in depth): rejects ungrounded numbers (must follow a tool call), investment content without educational framing, SQL/API-key leakage, and out-of-bounds length — retry-once then safe fallback.
- **Compliance framing** enforced in the system prompt *and* the validator (educational-only; no specific buy/sell directives).
- **Conversation data isolation:** `chat_sessions`, `chat_messages`, `financial_memory`, `ai_response_feedback`, and `token_usage` carry `tenant_id` with **`FORCE ROW LEVEL SECURITY`** (verified: `app_user` reads 0 rows without tenant context). App-layer `user_id` checks scope within a tenant; RLS is the database backstop.
- **Cost/abuse control:** bounded tool results (aggregates only); **atomic** per-tier daily token budget — a single reserve-then-settle increment closes the check/increment race so concurrent turns can't blow the limit; AI rate limit (10/min/user).

## Known follow-ups (scheduled, not gaps in Phase 1)
- Extend RLS policies to business tables as they're added (Phase 2+), scoped via the same tenant context.
- WAF + secret rotation Lambda (Phase 6).
- Per-tenant API-key auth for white-label partners (Phase 7).
