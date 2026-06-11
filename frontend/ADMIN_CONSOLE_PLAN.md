# Admin Console, Billing & Analytics — Product & Design Plan

> **Status:** Draft v1.1 (reviewed for scale & safety) · **Owners:** Product Owners (you) + Frontend/Backend
> **Companion:** `frontend/FRONTEND_PLAN.md` (this expands §17 and resolves §28 decisions).
> **Scope:** the product-owner management console, the Stripe billing system, and the analytics
> stack — planned to the same handoff standard as the user app. **This is a plan, not code.**

This document plans three things the user app depends on operationally:
1. **Admin / product-owner console** — how you run the business day-to-day.
2. **Billing** — how tiers become revenue (Stripe).
3. **Analytics** — how you measure and decide.

Every admin feature names the **new backend** it requires, because the backend has **zero admin
routes today**. The plan is deliberately honest about that gap.

---

## 0. Decisions (resolved)

| Decision | Resolution | Rationale |
|---|---|---|
| Admin in v1? | **Design-complete now; build as a fast-follow (Phase F5).** User app ships first. | The user app is fully backed by existing APIs and delivers value immediately. Admin needs an entire new backend (RBAC + admin APIs). Designing now lets backend + admin UI run in parallel without blocking launch. |
| Billing at launch? | **Display-only tiers at launch + Stripe-ready architecture; real Stripe as the immediate billing fast-follow (Phase F-Billing).** | Don't gate launch on PCI/checkout/dunning. Architect for Stripe from day one so switching it on is config + webhooks, not a rewrite. |
| Analytics vendor | **PostHog, self-hosted, consent-gated, zero PII.** | Privacy-first, owns its own data (fits a finance product), feeds the admin KPI dashboard, open-source. |

---

## Table of contents
1. Goals & non-goals
2. Roles & RBAC permission matrix
3. Admin authentication & security model
4. Admin information architecture & navigation
5. Admin pages — full specifications
6. Required backend API surface (the new contract)
7. Cross-tenant data access — the safe pattern
8. Billing plan (Stripe)
9. Analytics plan (PostHog)
10. Admin design language
11. Audit, compliance & data governance
12. Delivery roadmap
13. Definition of Done
14. Open decisions & assumptions

---

## 1. Goals & non-goals

**Goals.** Give product owners everything needed to operate the product safely: see health and
cost, support users, control access and features, monitor the AI/Plaid/alerts pipelines, manage
billing, and have a complete, tamper-evident audit trail.

**Non-goals (v1).** No data-science notebooks, no marketing automation, no multi-org reseller
panel (white-label is later), no in-console SQL. Keep it operational, not a BI suite — BI lives in
PostHog dashboards that the console links to.

---

## 2. Roles & RBAC permission matrix

Four roles. Least-privilege by default; every write is audited.

| Capability | Analyst | Support | Owner | Super-admin |
|---|---|---|---|---|
| View KPIs / dashboards | ✅ | ✅ | ✅ | ✅ |
| View user list/detail (PII-masked) | ✅ (masked) | ✅ | ✅ | ✅ |
| Unmask PII (audited) | ❌ | ✅ | ✅ | ✅ |
| Verify / resend / suspend user | ❌ | ✅ | ✅ | ✅ |
| Change user tier (comp/grant) | ❌ | ❌ | ✅ | ✅ |
| **Impersonate user** (time-boxed, audited) | ❌ | ✅ | ✅ | ✅ |
| View AI ops / token spend | ✅ | ✅ | ✅ | ✅ |
| Set AI cost caps | ❌ | ❌ | ✅ | ✅ |
| Plaid ops / trigger re-sync | ❌ | ✅ | ✅ | ✅ |
| Edit notification templates | ❌ | ❌ | ✅ | ✅ |
| Retry outbox | ❌ | ✅ | ✅ | ✅ |
| Feature flags / tier config | ❌ | ❌ | ✅ | ✅ |
| Billing: view revenue | ✅ | ✅ | ✅ | ✅ |
| Billing: refund / comp | ❌ | ❌ | ✅ | ✅ |
| View audit log | ✅ | ✅ | ✅ | ✅ |
| Manage admins / roles | ❌ | ❌ | ❌ | ✅ |

RBAC is enforced **server-side** (every admin endpoint checks role); the UI hides/disables
controls as a convenience only, never as the security boundary.

---

## 3. Admin authentication & security model

The admin surface is the **highest-risk** part of the system — it can read across tenants. The
model:

- **Separate identity** from end users: an `admins` table (or `users.is_admin`+`admin_role`),
  distinct from the consumer auth path.
- **Separate JWT audience** (e.g. `aud: financial-advisor-admin`) so a user token can never reach
  an admin route and vice-versa.
- **MFA mandatory** (TOTP) for all admin logins.
- **Short sessions** (e.g. 30-min access, idle timeout) + re-auth ("sudo mode") required before
  high-risk actions (impersonation, tier change, refund, role management).
- **Optional IP allowlist** (office/VPN) for owner/super-admin.
- **Every action audited** to `audit_logs` with actor admin id, target, before/after, IP, reason.
- **Impersonation** is time-boxed, requires a typed reason, shows a persistent "You are viewing as
  <user>" banner, is read-biased (configurable), and is fully logged + alertable.
- **No RLS bypass for the app role** — admin reads use audited `SECURITY DEFINER` functions/views
  (see §7), preserving FORCE RLS for the normal app.
- **Admin WAF/rate limits** stricter than the user app; brute-force lockout on admin login.

---

## 4. Admin information architecture & navigation

```
/admin/login                  (MFA)
/admin                        Overview (KPIs)
/admin/users                  Users — list / detail
/admin/ai                     AI operations & cost
/admin/plaid                  Plaid operations
/admin/notifications          Templates & outbox
/admin/alerts                 Alert-engine monitor
/admin/billing                Revenue & subscriptions
/admin/flags                  Feature flags & tier config
/admin/audit                  Audit log viewer
/admin/content                Marketing/legal CMS
/admin/settings               Admins & RBAC (super-admin)
```
Distinct admin chrome (denser, neutral theme) to avoid being mistaken for the user app. Global
search (users by email/id), role-aware nav (items hidden if not permitted).

---

## 5. Admin pages — full specifications

Each: **purpose · layout · components · data (new backend) · states · permissions.**

### /admin/login
- MFA login (email+password → TOTP). Lockout on brute force. No enumeration.
- New backend: admin auth endpoints (§6).

### /admin — Overview (KPIs)
- **Purpose:** is the business healthy right now?
- **Layout:** KPI StatCards (signups today/7d/30d, DAU/MAU, activation = linked-bank+1 plan,
  AI calls + error rate + token spend + est. cost, alert volume, MRR), trend charts, incident
  strip (AI degradation tier, Plaid failures, outbox DLQ depth).
- **Data:** `/admin/metrics` aggregates + existing `/metrics` (Prometheus) + PostHog funnels.
- **Scale (1M users):** KPIs are **pre-aggregated** (nightly/▵ rollup tables or a materialized
  view, cached with a short TTL) — **never** computed live with `COUNT(*)` over millions of rows on
  each dashboard load. Trends read from the rollup; "as of <time>" is shown. PostHog handles
  funnels/cohorts so the app DB isn't taxed for BI.
- **States:** loading skeletons, "no data yet" (pre-launch), stale-rollup hint, incident-active banner.
- **Permissions:** all roles.

### /admin/users — list + detail
- **List:** searchable/filterable table (email, tier, verified, status, created, last active,
  #banks). PII masked for analysts. Pagination (keyset).
- **Detail:** profile, tier, verification, linked Plaid items + sync status, budgets/goals counts,
  AI usage (token spend), recent audit events for this user. **Actions** (role-gated): resend
  verification, verify, **suspend/unsuspend**, change tier, reset password, **impersonate**
  (reason + sudo), unmask PII (audited).
- **Data:** `/admin/users` list/detail/patch; suspend flag; impersonation token (§6).
- **States:** empty search, suspended badge, item-error highlights, action confirmations.
- **Permissions:** per the matrix (§2).

### /admin/ai — AI operations & cost
- **Purpose:** keep the advisor healthy and affordable.
- **Layout:** live degradation tier (`/health/ai`), provider call/error rates, validation-failure
  rate, fallback events (Claude→Groq), **per-day token spend + estimated cost** trend, top spenders,
  **cost-cap controls** (daily $ cap, per-tier token budgets).
- **Data:** surface `/metrics` + `token_usage` aggregates; cap config endpoint (§6).
- **States:** healthy / tier-1 warn / tier-2 critical banner; cap-exceeded indicator.
- **Permissions:** view all; set caps owner+.

### /admin/plaid — Plaid operations
- **Purpose:** keep bank connections flowing.
- **Layout:** item health table (status, last sync, institution), failed `sync_jobs`, webhook log
  (recent events, signature status), **manual re-sync** trigger per item.
- **Data:** `/admin/plaid/items`, sync-job status reads, re-sync trigger (§6). Built on existing
  idempotent `run_sync_for_item`.
- **States:** all-healthy, items-in-error list, re-sync queued/running.
- **Permissions:** view all; re-sync support+.

### /admin/notifications — templates & outbox
- **Purpose:** control what gets sent and recover failures.
- **Layout:** template editor (email/push copy with variables + live preview + test-send),
  `notification_outbox` viewer (status, channel, dedupe key), **retry failed** action.
- **Data:** template store CRUD; outbox query; retry endpoint (§6). Outbox table already exists.
- **States:** template draft/published, outbox empty, failed-rows highlighted.
- **Permissions:** edit templates owner+; retry support+.

### /admin/alerts — alert-engine monitor
- **Purpose:** confirm the proactive layer is running.
- **Layout:** run history (scan time, users scanned, notifications dispatched, errors), per-type
  breakdown, last-run freshness.
- **Data:** run-history surfacing of the existing alert runner (§6).
- **States:** healthy cadence, stale-run warning, error spike.
- **Permissions:** view all.

### /admin/billing — revenue & subscriptions
- **Purpose:** see and manage money in.
- **Layout:** MRR/ARR, active subs by tier, churn, failed payments (dunning), subscription detail
  per user, **refund / comp** actions.
- **Data:** Stripe-backed `/admin/billing` reads + refund (§6, §8).
- **States:** pre-Stripe = "billing not yet enabled" placeholder; post-Stripe live data.
- **Permissions:** view all; refund/comp owner+.

### /admin/flags — feature flags & tier config
- **Purpose:** toggle features and tune tiers without a deploy.
- **Layout:** flag list (on/off, %, by-tier), **tier config editor** (token budgets, advisor depth,
  feature gates) — today these are env constants; this makes them data-driven.
- **Data:** flags + config table/API (§6).
- **States:** flag dirty/saved, config validation.
- **Permissions:** owner+.

### /admin/audit — audit log viewer
- **Purpose:** tamper-evident record of who did what.
- **Layout:** searchable/filterable table (actor, action, target, IP, time, before/after),
  export. Highlights admin actions (impersonation, tier changes, refunds, role changes).
- **Data:** `/admin/audit` over existing `audit_logs` (§6).
- **States:** filtered empty, high-risk-action emphasis.
- **Permissions:** view all (immutable — no edit/delete from UI).

### /admin/content — CMS
- **Purpose:** edit pricing/FAQ/legal without a deploy.
- **Layout:** simple content editor (MDX or content table) with preview + publish.
- **Permissions:** owner+.

### /admin/settings — admins & RBAC
- **Purpose:** manage the admin team.
- **Layout:** admin list, invite, assign role, disable, reset MFA, view each admin's recent
  actions.
- **Data:** admin/roles CRUD (§6).
- **States:** pending invite, disabled admin.
- **Permissions:** super-admin only.

---

## 6. Required backend API surface (the new contract)

> All under `/api/v1/admin/*`, admin-JWT + role-checked, every write audited. **None exist today.**

| Endpoint (proposed) | Purpose |
|---|---|
| `POST /admin/auth/login` `/mfa` `/refresh` `/logout` | admin auth + MFA |
| `GET /admin/metrics` | KPI aggregates (signups, DAU/MAU, activation, cost, MRR) — served from **pre-aggregated rollups/materialized views**, not live counts over millions of rows |
| `GET /admin/users` `GET /admin/users/{id}` `PATCH /admin/users/{id}` | list/detail/update (tier, suspend, verify) |
| `POST /admin/users/{id}/impersonate` | time-boxed, audited impersonation token |
| `POST /admin/users/{id}/resend-verification` `…/reset-password` | support actions |
| `GET /admin/ai/overview` `PUT /admin/ai/caps` | AI health + token spend; cost caps |
| `GET /admin/plaid/items` `GET /admin/plaid/sync-jobs` `POST /admin/plaid/items/{id}/resync` | Plaid ops |
| `GET/POST/PUT /admin/notification-templates` `GET /admin/outbox` `POST /admin/outbox/{id}/retry` | templates + outbox |
| `GET /admin/alerts/runs` | alert-engine run history |
| `GET /admin/billing/subscriptions` `POST /admin/billing/{id}/refund` | revenue + refunds |
| `GET/PUT /admin/flags` `GET/PUT /admin/tier-config` | flags + tier config |
| `GET /admin/audit` | audit query |
| `GET/POST/PUT /admin/admins` | RBAC management (super-admin) |

**Supporting backend work:** `admins`/role model + admin-JWT audience; role-checked middleware;
audited `SECURITY DEFINER` aggregate views; `suspended` flag + `stripe_customer_id` on `users`;
`subscriptions`, `notification_templates`, `feature_flags`, `tier_config` tables; impersonation
token issuance + audit; admin rate-limits/WAF.

---

## 7. Cross-tenant data access — the safe pattern

The app's whole security model is **FORCE RLS** + a non-owner `app_user` role. Admin must read
across tenants **without** weakening that:
- Admin queries go through **dedicated `SECURITY DEFINER` functions/views** (like the existing
  `list_users_for_scan` / `resolve_plaid_item`) that are narrowly scoped, audited, and owned by a
  role that can see across tenants — the normal `app_user` still **never** bypasses RLS.
- Admin endpoints run under the admin identity, log every read of sensitive data, and **mask PII**
  unless an authorized role explicitly unmasks (audited).
- No raw cross-tenant `SELECT *`; each admin view returns only the fields a screen needs.

This keeps the §17/§21 guarantees intact: a bug in admin code can't silently exfiltrate a tenant's
data, because access is funneled through a small set of audited, purpose-built functions.

---

## 8. Billing plan (Stripe)

**Launch posture:** tiers shown, **display-only** (no charge); architecture is Stripe-ready.
**Fast-follow (F-Billing):** switch on real billing.

**Design:**
- **Checkout:** Stripe Checkout (hosted) for v1 (fastest PCI-safe path); Elements later if we want
  in-app.
- **Customer Portal:** Stripe-hosted for plan change / card update / cancel (no custom UI to
  maintain).
- **Plans:** Free / Plus / Premium, monthly + annual price IDs; map Stripe subscription → `users.tier`.
- **Webhooks:** `checkout.session.completed`, `customer.subscription.created/updated/deleted`,
  `invoice.payment_failed` → backend updates tier, handles **dunning** (grace + downgrade on final
  failure), proration on up/downgrade.
- **Source of truth:** Stripe for subscription state; `users.tier` is the synced cache that gates
  the app (token budgets, advisor depth).
- **Tax/compliance:** Stripe Tax; invoices/receipts via Stripe; SCA handled by Checkout.
- **Admin:** `/admin/billing` reads subscriptions, shows MRR/churn/dunning, allows refund/comp.

**Backend needed:** `stripe_customer_id` on users, `subscriptions` table, `/billing/*` (create
checkout session, portal link), `/webhooks/stripe` (signature-verified, idempotent — mirrors the
Plaid-webhook discipline), tier-sync logic.

**Frontend:** Pricing → Checkout redirect; Settings/Billing → Customer Portal link + current plan +
token-budget meter; upgrade prompts at tier limits (advisor budget exhausted, etc.).

---

## 9. Analytics plan (PostHog)

**Choice:** PostHog, **self-hosted**, **consent-gated**, **zero PII** (no emails/amounts in
events; user identified by opaque id only).

**What we measure:**
- **Activation funnel:** signup → verify → first bank link → first budget/goal → first advisor chat.
  Activation = linked bank + 1 plan object.
- **Engagement:** WAU/MAU, advisor usage by tier, feature adoption.
- **Monetization:** upgrade-prompt → checkout → subscribe; tier mix; churn signals.
- **Reliability (RUM):** Core Web Vitals, error rate by `code`, AI degradation impact on usage.

**Event taxonomy (allowlisted props only):** `signup_started/completed`, `email_verified`,
`bank_link_started/succeeded/failed`, `budget_created`, `goal_created`, `advisor_message_sent`,
`advisor_feedback`, `upgrade_prompt_shown/clicked`, `checkout_started/completed`,
`error_shown{code}`.

**Governance:** consent banner gates analytics + session replay (replay masks all inputs);
no money values or PII in any event; retention policy set; the **admin Overview** embeds/links
PostHog dashboards so owners see funnels next to operational KPIs.

---

## 10. Admin design language

- Reuses the design tokens (§4 of the main plan) but with a **distinct neutral admin theme** and
  **denser layout** (data tables, compact spacing) so it's visually unmistakable vs. the user app.
- Components: DataTable (sortable/filterable/paginated/exportable), DetailDrawer, AuditTrailList,
  ConfirmDangerDialog (typed confirmation for destructive/impersonation), RoleBadge, KpiCard,
  IncidentBanner, JsonDiff (before/after for audit).
- All admin tables: server-side pagination (keyset), column-level PII masking, empty/error/loading
  states, CSV export.
- Accessibility + responsive still apply (admins use laptops primarily; tables degrade to detail
  cards on small screens).

---

## 11. Audit, compliance & data governance

- **Every admin write** → `audit_logs` with actor, target, before/after, IP, reason; surfaced in
  `/admin/audit`; high-risk actions (impersonation, tier change, refund, role change, PII unmask)
  flagged and optionally alerted to owners.
- **Immutable** audit (no UI edit/delete).
- **PII minimization:** masked by default; unmask is a privileged, logged action.
- **Data governance:** user data-export and delete (from the user app) reflected in admin; deletion
  cascades (matches Plaid-disconnect purge behavior).
- **SOC 2 alignment:** the audit + RBAC + least-privilege model is built to support a future audit;
  claims only made once achieved.

---

## 12. Delivery roadmap

> Admin is **Phase F5** in the main roadmap; billing is **F-Billing**; analytics threads through F0+.

| Phase | Scope | Exit criteria |
|---|---|---|
| **F0+ (with user app)** | PostHog wired, consent banner, activation funnel events | funnel visible in PostHog |
| **F-Billing** (after F1) | Stripe Checkout + Portal + webhooks + tier sync; Pricing/Settings billing live | a real upgrade charges and flips `tier` |
| **F5a — Admin (read-only)** | admin auth+MFA, RBAC, Overview, Users (view), AI ops, Plaid ops, Alerts, Audit viewer | owners can monitor + support (read) safely |
| **F5b — Admin (write)** | suspend/tier/impersonate, template editor + outbox retry, re-sync, flags/tier-config, billing refunds, RBAC mgmt | owners can fully operate the product |

**Hard dependency:** F5 needs the new admin backend (§6) + cross-tenant SECURITY DEFINER views
(§7). Backend and admin UI can proceed in parallel from the contract.

---

## 13. Definition of Done (admin features)

- [ ] Role-gated **server-side**; UI hides/disables per role (convenience only).
- [ ] Every write audited (actor/target/before-after/IP/reason) and visible in `/admin/audit`.
- [ ] PII masked by default; unmask logged.
- [ ] Cross-tenant reads only via audited SECURITY DEFINER (no app-role RLS bypass).
- [ ] All table states: loading/empty/error/filtered-empty; server pagination; export.
- [ ] Destructive/impersonation actions require sudo re-auth + typed confirmation.
- [ ] a11y + responsive; admin theme distinct from user app.
- [ ] Tests: RBAC matrix enforced (unit/integration), e2e for impersonation + suspend + refund.

---

## 14. Open decisions & assumptions

**Decisions still needed:**
1. **Admin identity model:** `users.is_admin`+role vs. a separate `admins` table. *(Recommend
   separate `admins` table — cleaner blast-radius isolation.)*
2. **IP allowlist** for owner/super-admin at launch? *(Recommend optional, on for super-admin.)*
3. **Session replay** in PostHog (with input masking) — on or off at launch? *(Recommend off until
   privacy review.)*
4. **Stripe go-live timing** relative to user-app launch (immediately after F1, or later).

**Assumptions:** single org (no white-label admin yet); admins are internal staff; PostHog
self-hosted on our infra; Stripe Checkout (hosted) for v1; USD billing first.

---

*End of plan v1.0. This plans the operational layer; implementation waits on your go-ahead and the
new admin backend contract (§6).*
