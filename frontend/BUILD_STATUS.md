# Frontend Build Status & Pending Work

> **Working brand:** MoneyWealth AI (provisional). **Stack:** Next.js 16, React 19, Tailwind 4, TypeScript.
> Roadmap reference: [FRONTEND_PLAN.md §26](FRONTEND_PLAN.md) · Admin/Billing: [ADMIN_CONSOLE_PLAN.md](ADMIN_CONSOLE_PLAN.md)
> Legend: ✅ done · 🟡 partial · ⏳ built-but-needs-a-key · ⬜ not started

## Snapshot

| Phase | State | Blocker to finish |
|---|---|---|
| F0 Foundation | ✅ | — |
| F1 Core money | 🟡 | Plaid sandbox keys (Accounts) |
| F2 Advanced | ✅ | — (Debt/Portfolio show empty states until a bank is linked) |
| F3 AI Advisor | ⏳ | `ANTHROPIC_API_KEY` or `GROQ_API_KEY` (UI is complete) |
| F4 Marketing | ✅ | Counsel-approved legal copy |
| F-Billing | ⬜ | Stripe keys **+ new backend** |
| F5 Admin console | ⬜ | **Entire new admin backend** (RBAC + APIs) |
| F6 Polish | ✅ | — |

---

## F0 — Foundation ✅
Done: Next.js scaffold, design system (ink/aurora/glass tokens), primitives (Button, Panel, Money,
Badge, Input, Select, MoneyInput, Toggle, Dialog), brand logo, app shell (sidebar + topbar), auth
(BFF: signup/login/logout/refresh/verify/resend + authed proxy), in-memory access token +
httpOnly refresh cookie, strict nonce CSP + security headers.

**Pending / nice-to-have**
- Real brand name + logo set (current mark is provisional) and real **PWA icons** (192/512 maskable PNGs).
- Password reset flow (`/forgot`, `/reset`) — **needs backend endpoints**.
- Active-sessions list + revoke in Settings → **needs backend endpoints**.

## F1 — Core money 🟡
Done: **Budgets** (CRUD, pacing bars, delete-with-undo), **Goals** (CRUD, future-date rule, rings),
**Dashboard** (real budget/goal summaries). All live against the backend.

**Pending**
- ⏳ **Accounts / Plaid Link** page + connect flow — **needs Plaid sandbox keys** (`PLAID_CLIENT_ID`,
  `PLAID_SECRET`, `PLAID_ENC_KEY`) in the backend. Until then "Connect a bank" returns `PLAID_ERROR`.
- ⬜ **Transactions** page (browse/search/filter) — **needs a backend `GET /transactions`** endpoint
  (paginated/filterable); today transactions are only read inside AI tools/dashboards.
- Net-worth on the dashboard is gated on linked accounts (empty state until Plaid).

## F2 — Advanced ✅
Done: **Settings** (profile + notification preferences + quiet hours/timezone — fully live),
**Notifications** feed (list, mark-read, mark-all, unread badge), **Debt** dashboard
(summary + snowball/avalanche payoff what-if), **Portfolio** dashboard (allocation, P/L, holdings,
concentration).

**Pending**
- Debt & Portfolio render **empty states until a bank/brokerage is linked** (data comes from Plaid).
- Goal "contribute" is via edit; a dedicated quick-add affordance would be nicer.

## F3 — AI Advisor ⏳ (UI complete)
Done: streaming-style chat (typewriter), suggested prompts, **tool-call chips** ("↳ checked …"),
👍/👎 feedback wired, token/tier hint, graceful `AI_UNAVAILABLE` / `RATE_LIMITED` states, disclaimer.

**Pending**
- ⏳ **Live responses need an AI key** (`ANTHROPIC_API_KEY` or free-tier `GROQ_API_KEY`) in the backend.
- Conversation **history sidebar** (list past chats via `GET /advisor/chats/{id}/messages`) — not built.
- True server-sent streaming (backend currently returns a single response; UI simulates streaming).

## F4 — Marketing ✅
Done: landing, `/features`, `/pricing` (monthly/annual toggle + FAQ), `/security`, `/about`,
`/legal/{terms,privacy,disclosures}`, rich footer, SEO metadata, route-group layout.

**Pending**
- ⚠️ **Legal pages are templates** — replace with **counsel-approved** Terms/Privacy/Disclosures before launch.
- Real **OG share image** (currently text-only OG tags; no image asset).
- Social proof / testimonials are placeholders.

## F-Billing — Stripe ⬜ (not started)
Needs **frontend + new backend**.
- Frontend: Pricing → Stripe Checkout redirect; Settings → Billing (Customer Portal link, current plan,
  token-budget meter); upgrade prompts at tier limits.
- **Backend (new):** `stripe_customer_id` on users, `subscriptions` table, `/billing/*` (create
  checkout session, portal link), signature-verified `/webhooks/stripe` that syncs `users.tier`,
  dunning/proration handling. **Needs Stripe keys.**

## F5 — Admin console ⬜ (not started, biggest lift)
Needs **frontend + an entire new admin backend** (there are **zero admin routes today**).
See [ADMIN_CONSOLE_PLAN.md](ADMIN_CONSOLE_PLAN.md). Backend prerequisites:
- Admin identity + RBAC (owner/support/analyst/super-admin), admin-JWT audience, **mandatory MFA**.
- Audited cross-tenant `SECURITY DEFINER` views (never weaken the app role's FORCE RLS).
- ~12 `/admin/*` endpoints (metrics, users, AI ops + cost caps, Plaid ops, templates/outbox,
  alerts runs, flags/tier-config, audit, billing, RBAC mgmt).
- Pre-aggregated KPI rollups (don't `COUNT(*)` millions of rows per dashboard load).

Frontend then: admin auth + MFA, distinct admin chrome, DataTable/DetailDrawer/AuditTrail/ConfirmDanger,
read-only screens first → write actions (suspend/tier/impersonate/refund).

## F6 — Polish ✅
Done: per-segment **error boundaries** (app + marketing + global), branded **404**, app **loading**
skeleton, **mobile nav drawer**, **SEO/PWA** (OG, manifest, robots, sitemap, theme-color),
**skip-to-content** + `main` landmarks.

**Pending / future polish**
- **Automated test suite** — none yet: unit (Vitest), component (Storybook/Testing Library), **e2e
  (Playwright)**, **a11y (axe in CI)**, visual regression. (Plan §24.)
- **Analytics** — PostHog wiring + consent banner + funnels (Plan §23) not implemented.
- **i18n** — copy is inline English; no message catalogs yet (Plan §22 scaffolding).
- **Lighthouse CI / bundle-size budget** gates not wired (Plan §20).
- Full manual a11y pass (NVDA/VoiceOver) + reduced-motion spot-checks.
- Maintenance-mode flag/page (driven by a feature flag) — deferred.
- Real OG image generation route.

---

## Cross-cutting backend dependencies (summary)
| To finish | Provide / build |
|---|---|
| Accounts (F1) | Plaid sandbox keys |
| Transactions (F1) | backend `GET /transactions` |
| Live Advisor (F3) | `ANTHROPIC_API_KEY` or `GROQ_API_KEY` |
| Real verification emails | backend `MAIL_TRANSPORT=smtp/sendgrid` + creds |
| Password reset / sessions | backend auth endpoints |
| Billing (F-Billing) | Stripe keys + Stripe backend |
| Admin (F5) | full admin backend + RBAC |

## Local run
```
# backend (port 3000 was taken on this machine → we used 8000)
cd backend && .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
# frontend (BFF points at backend via frontend/.env.local → API_BASE_URL)
cd frontend && npm run dev -- --port 3100
```
