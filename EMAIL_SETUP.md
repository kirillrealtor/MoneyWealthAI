# Email Setup for Deployment (MoneyWealth AI)

Transactional email (verification links, password resets) is currently
**disabled in production** — `MAIL_TRANSPORT=console`, so the backend only
*logs* the link instead of sending it. This is deliberate: the personal Gmail
that was used as a temporary sender has been removed (see "What was removed"
below). This doc is the checklist to turn real email back on the right way.

> The app code needs **zero changes**. Email is fully config-driven
> (`backend/app/modules/auth/mailer.py`). You only set env vars + one secret.

---

## ⚠️ First: revoke the old credential

The Gmail **App Password** used earlier was shared in a chat, so treat it as
compromised:

1. Go to <https://myaccount.google.com/apppasswords>
2. Delete the app password named (e.g.) "MoneyWealth".

It no longer lives in AWS (the SSM secret was deleted), but revoking it at the
source is the safe move. Separately, the **admin login account** still uses a
personal email address; change it later if you want full separation (it's a DB
row in `users`, unrelated to sending email).

---

## Choose a path

| | **Option A — Dedicated Gmail** | **Option B — Amazon SES** *(recommended)* |
|---|---|---|
| Effort | ~5 min | ~30 min + domain |
| Cost | Free | ~$0.10 / 1,000 emails |
| Sending limit | ~500/day (free Gmail) | Millions (after prod access) |
| Deliverability | OK-ish (no brand domain) | Strong (DKIM/SPF on your domain) |
| From address | `something@gmail.com` | `no-reply@yourdomain.com` |
| Good for | Demo / hackathon | Real product / scale |

You already run everything on AWS, so **Option B (SES) is the real answer**.
Option A is a fine stopgap for a demo.

---

## Option A — Dedicated Gmail (stopgap)

1. Create a **new** Google account, e.g. `moneywealth.noreply@gmail.com`
   (do **not** reuse a personal account).
2. Turn on **2-Step Verification**: <https://myaccount.google.com/security>
3. Create an **App Password**: <https://myaccount.google.com/apppasswords>
   → copy the 16-char code (remove spaces).
4. Apply the config — see **"Wiring it into AWS"** below, using:
   - `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_STARTTLS=true`
   - `SMTP_USERNAME` = the new gmail, `MAIL_FROM` = the new gmail
   - secret `SMTP_PASSWORD` = the 16-char app password

## Option B — Amazon SES (recommended)

1. **Verify a domain** (or a single from-address to start) in SES:
   - Console → Amazon SES → **Identities** → Create identity → Domain
   - Add the **DKIM** CNAME records SES gives you to your DNS, plus an SPF
     record. Wait for "Verified".
   - (Region: use `us-east-1` to match the rest of the stack.)
2. **Request production access** (SES starts in *sandbox* — can only send to
   verified addresses): SES → Account dashboard → "Request production access".
   Approval is usually < 24h.
3. **Create SMTP credentials**: SES → **SMTP settings** → Create SMTP
   credentials (this makes an IAM user; you get an SMTP username + password —
   these are NOT your AWS keys).
4. Apply the config — see below, using SES SMTP values:
   - `SMTP_HOST=email-smtp.us-east-1.amazonaws.com`, `SMTP_PORT=587`,
     `SMTP_STARTTLS=true`
   - `SMTP_USERNAME` = SES SMTP username, secret `SMTP_PASSWORD` = SES SMTP
     password
   - `MAIL_FROM=no-reply@yourdomain.com` (must be on the verified domain)

> SES also has a native HTTP API, but our mailer speaks **SMTP**, so the SMTP
> endpoint above is plug-and-play. (`MAIL_TRANSPORT` stays `smtp`.)

---

## Wiring it into AWS (same for both options)

All commands use the AWS CLI (`python -m awscli ...`), region `us-east-1`,
account `346133548342`. On Git Bash, prefix SSM commands with
`MSYS_NO_PATHCONV=1` so the leading `/` in the parameter name isn't mangled.

**1. Store the password as an encrypted secret:**
```bash
MSYS_NO_PATHCONV=1 python -m awscli ssm put-parameter \
  --name "/moneywealth/SMTP_PASSWORD" --type SecureString \
  --value "<APP_PASSWORD_OR_SES_SMTP_PASSWORD>" --overwrite --region us-east-1
```

**2. Register a new task definition revision** that adds the SMTP env +
secret (start from the current rev, add these):
- environment: `MAIL_TRANSPORT=smtp`, `SMTP_HOST`, `SMTP_PORT=587`,
  `SMTP_STARTTLS=true`, `SMTP_USERNAME`, `MAIL_FROM`
- secrets: `SMTP_PASSWORD` →
  `arn:aws:ssm:us-east-1:346133548342:parameter/moneywealth/SMTP_PASSWORD`

(The execution role `ecsTaskExecutionRole` already has `mwSsmRead`, so it can
read the new secret — no IAM change needed.)

**3. Roll the service:**
```bash
python -m awscli ecs update-service --cluster moneywealth \
  --service moneywealth-backend --task-definition moneywealth-backend:<NEW_REV> \
  --force-new-deployment --region us-east-1
```

**4. Repoint the frontend (the Fargate IP changes on every roll):**
```bash
# get the new task's public IP
TASK=$(python -m awscli ecs list-tasks --cluster moneywealth \
  --service-name moneywealth-backend --desired-status RUNNING \
  --region us-east-1 --query "taskArns[0]" --output text)
ENI=$(python -m awscli ecs describe-tasks --cluster moneywealth --tasks "$TASK" \
  --region us-east-1 \
  --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value | [0]" \
  --output text)
python -m awscli ec2 describe-network-interfaces --network-interface-ids "$ENI" \
  --region us-east-1 --query "NetworkInterfaces[0].Association.PublicIp" --output text
# then update Vercel + redeploy
vercel env rm  API_BASE_URL production --yes  --token=$VERCEL_TOKEN --scope=24pwai0032-gifs-projects
echo "http://<NEW_IP>:8080" | vercel env add API_BASE_URL production --token=$VERCEL_TOKEN --scope=24pwai0032-gifs-projects
gh run rerun $(gh run list --workflow=deploy-frontend.yml --limit 1 --json databaseId -q '.[0].databaseId')
```

> This IP churn is the real long-term pain. The proper fix is a **stable
> endpoint** (HTTPS domain in front of the backend). That removes the
> repoint-on-every-deploy step entirely — see "Backend HTTPS" follow-up in
> `DEPLOY_SECRETS.local.md`.

---

## Verify it works

```bash
# 1. Sign up a test user (use a +alias so it lands in an inbox you control):
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  http://<NEW_IP>:8080/api/v1/auth/signup -H "content-type: application/json" \
  -d '{"email":"you+mwtest@gmail.com","password":"TestPass123!","full_name":"Test"}'

# 2. Confirm the send in logs (should show event "email sent", transport smtp):
python -m awscli logs filter-log-events --log-group-name /ecs/moneywealth-backend \
  --region us-east-1 --filter-pattern "email" --query "events[-1].message" --output text

# 3. Check the inbox → click the verify link → it should log you straight into /app.
```

If the send fails, the log shows `email send failed` with the SMTP error
(usually: wrong app password, 2FA not on, SES still in sandbox, or `MAIL_FROM`
not on a verified domain).

---

## What was removed (2026-06-21)

- SSM SecureString `/moneywealth/SMTP_PASSWORD` — **deleted**.
- Task def **rev 5** (had `SMTP_USERNAME`/`MAIL_FROM` = personal gmail) —
  **deregistered**. Live service is **rev 6**, `MAIL_TRANSPORT=console`.
- File/memory references to the personal gmail SMTP config — scrubbed.
- The personal Gmail App Password was never written to a file (SSM only).
