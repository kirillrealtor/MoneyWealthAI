# Deploying MoneyWealth AI (Vercel + AWS)

A pragmatic, decision-made path to get the app live. ~60–90 min the first time.
Architecture (matches the "Vercel + AWS Databases" stack):

```
Browser ──► Vercel (Next.js frontend + BFF)  ──► AWS App Runner (FastAPI backend)
                                                      │            │
                                              AWS RDS PostgreSQL   Upstash Redis
```

The browser only ever talks to Vercel (same-origin); the Next BFF calls the
backend server-side. So **no CORS is needed** and tokens stay first-party.

What I prepared for you (already in the repo): production `Dockerfile` (builds ✓),
`backend/apprunner.yaml` (App Runner config), and this runbook. The steps below
are the account-bound parts only you can do (AWS/Vercel logins).

---

## 0. Prerequisites
- AWS account (your $100 credits), Vercel account, the code pushed to GitHub (done).
- Locally: the backend `.venv` (to run migrations) and the AWS CLI signed in (optional).

## 1. Database — AWS RDS PostgreSQL
1. RDS → Create database → **PostgreSQL 16**, template **Free tier**, `db.t4g.micro`,
   20 GB. Set a master username (e.g. `fathom_admin`) + password. **Public access: Yes**
   (simplest; lock the security group to App Runner later). DB name: `financial_advisor`.
2. After it's up, copy the **endpoint**. Your two connection strings:
   - `MIGRATION_DATABASE_URL` (owner, runs DDL): `postgresql://fathom_admin:PASS@ENDPOINT:5432/financial_advisor`
   - `DATABASE_URL` (the app — a **non-owner** role you create in step 3).
3. **Create the app role + RLS isolation.** Connect as the master and run:
   ```sql
   CREATE ROLE app_user LOGIN PASSWORD 'another-strong-pass' NOBYPASSRLS;
   GRANT CONNECT ON DATABASE financial_advisor TO app_user;
   -- the migrations GRANT table/function access to app_user automatically.
   -- The admin console's cross-tenant functions are SECURITY DEFINER and must
   -- bypass RLS, so the OWNER (master) role needs BYPASSRLS:
   ALTER ROLE fathom_admin BYPASSRLS;
   ```
   Then `DATABASE_URL = postgresql://app_user:another-strong-pass@ENDPOINT:5432/financial_advisor`.

## 2. Redis — Upstash (free, serverless; simplest)
1. console.upstash.com → Create a Redis database (any region). Copy the
   **`rediss://...` URL** (TLS). That's your `REDIS_URL`.
   *(All-AWS alternative: ElastiCache Redis — needs a VPC + the backend in that VPC.)*

## 3. Run migrations (from your laptop, once)
```bash
cd backend
MIGRATION_DATABASE_URL="postgresql://fathom_admin:PASS@ENDPOINT:5432/financial_advisor" \
  .venv/Scripts/python.exe -m scripts.migrate
# Bootstrap your first admin:
DATABASE_URL="postgresql://app_user:...@ENDPOINT:5432/financial_advisor" \
  .venv/Scripts/python.exe -m scripts.create_admin you@yourco.com 'AStrongPass1!' super_admin
```

## 4. Backend — AWS App Runner
1. App Runner → Create service → **Source: GitHub** → connect the repo →
   **Source directory: `/backend`** → it auto-detects `apprunner.yaml`.
2. **Environment variables** (Configuration → Env vars / Secrets — never commit these):
   ```
   ENV=production
   ALLOWED_HOSTS=<your-apprunner-domain>            # e.g. xxxx.us-east-1.awsapprunner.com
   DATABASE_URL=postgresql://app_user:...@ENDPOINT:5432/financial_advisor
   MIGRATION_DATABASE_URL=postgresql://fathom_admin:...@ENDPOINT:5432/financial_advisor
   REDIS_URL=rediss://...upstash.io:6379
   JWT_ACCESS_SECRET=<openssl rand -base64 48>
   JWT_REFRESH_SECRET=<openssl rand -base64 48>
   WEB_APP_URL=https://<your-vercel-domain>
   COOKIE_DOMAIN=<your-vercel-domain>               # for the refresh cookie
   MAIL_TRANSPORT=resend
   MAIL_FROM=MoneyWealth AI <onboarding@resend.dev>
   RESEND_API_KEY=re_...                            # or inject via SSM (see DEVOPS_HANDOFF.md)
   MAGIC_LINK_TTL_MINUTES=15
   GROQ_API_KEY=...                                 # (or ANTHROPIC_API_KEY) for the advisor
   PLAID_ENV=sandbox  PLAID_CLIENT_ID=...  PLAID_SECRET=...  PLAID_ENC_KEY=...
   PLAID_PRODUCTS=transactions,liabilities,investments
   SYNC_WORKER_ENABLED=true                         # run the sync worker in-process (single instance)
   # Stripe (when activating billing): STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_*
   ```
3. Health check path: `/health`. Deploy. Note the service URL (the backend origin).
4. **Lock the RDS security group** to allow inbound 5432 only from App Runner's
   VPC connector / egress (or, for the hackathon, leave public but rotate creds after).

## 5. Frontend — Vercel
1. vercel.com → New Project → import the GitHub repo → **Root Directory: `frontend`**
   (Framework auto-detected as Next.js).
2. **Environment variables**:
   ```
   API_BASE_URL=https://<your-apprunner-backend-url>     # server-only (no NEXT_PUBLIC_)
   NEXT_PUBLIC_APP_URL=https://<your-vercel-domain>
   # optional: NEXT_PUBLIC_POSTHOG_KEY=phc_...
   ```
3. Deploy. Vercel gives you `https://<project>.vercel.app`.
4. Go back and set the backend's `WEB_APP_URL` + `COOKIE_DOMAIN` to this domain, and
   `ALLOWED_HOSTS` to the App Runner domain; redeploy the backend.

## 6. Smoke test (the go-live checklist)
- `curl https://<backend>/health` → `{"status":"ok"}`; `/health/ready` → db+redis ok.
- Open the Vercel URL → sign up → verify (check email or backend logs) → log in → dashboard.
- Link a Plaid sandbox bank → Transactions/Debt/Portfolio populate.
- Ask the advisor a question (needs the AI key).
- `/admin/login` with the admin you created → **Overview KPIs load** (this confirms the
  SECURITY DEFINER + BYPASSRLS from step 1.3 is correct — if KPIs are empty, re-check it).

## Security must-dos before real users
- `ENV=production` **rejects `ALLOWED_HOSTS=*`** at startup — set explicit hosts (done above).
- Rotate any keys that ever touched a shared chat. Use real secrets (48-byte JWT secrets).
- Move secrets to **AWS Secrets Manager** and reference them from App Runner (don't paste
  long-term). Enable RDS automated backups (PITR). Put **Stripe in live mode** only when ready.
- The full 1M-scale topology (RDS Proxy, ElastiCache Multi-AZ, ECS worker fleet, WAF) is in
  `backend/docs/PRODUCTION_DEPLOYMENT.md` — graduate to it as you grow.

---

### What needs *you* (account-bound, I can't do these for you)
Creating the RDS instance, the Upstash DB, the App Runner service, and the Vercel
project all require your AWS/Vercel logins + 2FA. Everything else (Dockerfile,
apprunner.yaml, migrations, the app itself) is done. If you authenticate the AWS &
Vercel CLIs in your terminal, I can help script some of these steps — otherwise
follow the clicks above and tell me where you get stuck.
```
