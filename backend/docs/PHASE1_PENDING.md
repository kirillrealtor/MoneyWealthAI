# Phase 1 — Deferred Items & Required Inputs

Things that are **built but not yet activated**, or that **need credentials/decisions from you** before Phase 1 is production-ready. Code is in place behind interfaces/flags; these are the activation steps, not new development.

Legend: 🔑 needs an account/key from you · ⚙️ config/infra step · 🧩 small code adapter

---

## 1. Transactional email (verification emails)
**Status:** mechanism built (single-use token, 24h expiry, `verify-email` endpoint). Delivery is a **console stub** — emails are logged, not sent. Decision deferred.

To activate before launch:
- 🔑 Pick a provider: **AWS SES** (cheapest at scale, AWS-native; needs domain auth) or **Postmark** (best deliverability, simplest).
- ⚙️ Stand up a sending domain (e.g. `mail.yourapp.com`) with **DKIM + SPF + DMARC**. For SES, also request production access (removes sandbox).
- 🔑 Put the provider API key in **AWS Secrets Manager**.
- 🧩 Implement the provider branch in `app/modules/auth/mailer.py` `send_mail()` (interface already abstracted — ~30 lines, no caller changes).
- ⚙️ Set `MAIL_TRANSPORT=ses|sendgrid` and `MAIL_FROM`.

## 2. Captcha (Cloudflare Turnstile)
**Status:** fully wired and tested — **disabled by default** (no-op) so dev/test run without a key. Required on signup; step-up on login after 3 fails.

To activate in staging/production:
- 🔑 Create a Cloudflare Turnstile site → get **site key** (frontend) + **secret key** (backend).
- 🔑 Store the secret in **AWS Secrets Manager**; inject as `TURNSTILE_SECRET_KEY`.
- ⚙️ Set `TURNSTILE_ENABLED=true` (optionally tune `LOGIN_CAPTCHA_AFTER_FAILS`, default 3).
- 🧩 Frontend: render the Turnstile widget with the site key and send the token as `captcha_token` on signup/login.

## 3. Database — production RLS role
**Status:** ✅ **Active in production** on Aurora PostgreSQL via RDS Proxy.

- `app_user` (NOBYPASSRLS) — app connects via `DATABASE_URL` → proxy endpoint.
- `mwadmin` (BYPASSRLS) — migrations via `MIGRATION_DATABASE_URL` → proxy endpoint;
  `ALTER ROLE mwadmin BYPASSRLS` applied for admin SECURITY DEFINER functions.
- Passwords in **Secrets Manager**; connection strings in **SSM** (URL-encoded).
- Local dev still uses docker-compose Postgres + migration `003` dev `app_user` block.

## 4. Secrets & config (no secrets in env files in prod)
- 🔑 Move to **AWS Secrets Manager**: DB URLs, `JWT_ACCESS_SECRET`, `JWT_REFRESH_SECRET`, Turnstile secret, email provider key.
- ⚙️ Set production `ALLOWED_HOSTS` (real domains) and `CORS_ORIGINS` (real frontend origin). `*` host is dev-only.
- ⚙️ Rotate JWT secrets on a schedule (rotation invalidates active sessions — plan the window).

## 5. Transport / edge (Phase 6 hardening, noted here for completeness)
- ⚙️ TLS termination + **HSTS** is emitted in prod; ensure the LB/CDN doesn't strip it.
- ⚙️ **AWS WAF** in front of the API (rate/bot rules) — complements app-layer throttle.
- ⚙️ Confirm `MAX_BODY_BYTES` matches the largest legitimate payload (default 1 MB).

---

## Quick activation checklist (pre-launch)
- [ ] Email provider chosen, domain DKIM/SPF/DMARC verified, `send_mail()` adapter shipped
- [ ] Turnstile site created; `TURNSTILE_ENABLED=true` + secret in Secrets Manager; frontend widget live
- [x] `app_user` role provisioned; app on RDS Proxy as `app_user`; verified `NOBYPASSRLS`
- [ ] All secrets in Secrets Manager; no secrets in committed env files
- [ ] Production `ALLOWED_HOSTS` + `CORS_ORIGINS` set
- [ ] WAF + TLS/HSTS verified at the edge
