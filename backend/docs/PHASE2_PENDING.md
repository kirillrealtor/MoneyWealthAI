# Phase 2 (Plaid) — Deferred Items & Required Inputs

The Plaid data layer is built and tested with a mocked client. To run it live you
supply credentials/config; the code is environment-agnostic (sandbox →
production is config only).

Legend: 🔑 key/account · ⚙️ config/infra · 🧩 small code

## To run live (sandbox first)
- 🔑 Create a Plaid account → **`PLAID_CLIENT_ID`** + **sandbox `PLAID_SECRET`** (free).
- ⚙️ Set `PLAID_ENV=sandbox`, `PLAID_PRODUCTS`, `PLAID_COUNTRY_CODES`.
- 🔑 Generate **`PLAID_ENC_KEY`** (base64 of 32 random bytes) for token encryption:
  `python -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())"`
- 🧩 Frontend: render **Plaid Link** with the `link_token` from `POST /plaid/link-token`,
  then send the returned `public_token` to `POST /plaid/exchange`.

## To enable webhooks
- ⚙️ A public HTTPS URL → set `PLAID_WEBHOOK_URL=https://.../api/v1/webhooks/plaid`
  (and Plaid dashboard webhook). Signature verification is already enforced.

## Going to production
- 🔑 Plaid **production access** approval + production `PLAID_SECRET`; set `PLAID_ENV=production`.
- ⚙️ **`PLAID_ENC_KEY` from AWS KMS / Secrets Manager** (not a file). Plan key
  rotation: blobs are versioned (byte 0); add a key-by-version lookup when you rotate.
- ⚙️ Move sync off the web process onto **SQS + a worker fleet** (currently a
  fire-and-forget asyncio task — see `service._spawn_sync`). The sync function is
  already idempotent and concurrency-locked, so this is a transport swap.
- ⚙️ Automate **monthly `transactions` partition creation** (cron, 1 month ahead).
- ⚙️ Add **investments/liabilities sync** calls to the worker (client methods exist).

## Security already enforced (no action needed)
- Access tokens AES-256-GCM encrypted at rest, AAD-bound to user, never logged.
- Webhooks verified (ES256 JWT + JWK + body SHA-256 + freshness) before any action.
- FORCE RLS + tenant scoping on every Plaid table; cross-tenant webhook lookup via
  a single audited `SECURITY DEFINER` resolver.
- Idempotent sync (cursor + `ON CONFLICT` + Redis per-item lock).
- Endpoints gated (auth + verified email), rate-limited; disconnect revokes at
  Plaid and purges local data.
