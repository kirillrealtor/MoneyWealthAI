# Frontend Product & Design Specification — AI Financial Advisor

> **Status:** Draft v1.1 (reviewed for 1M-user scale, resilience & friendliness) · **Owners:** Product Owners (you) + Frontend
> **Working brand:** *TBD — shared later; referenced as **Fathom** throughout as a placeholder, a one-token rename (see §3)*
> **Scope:** the complete web product — marketing site, authenticated user app, and the
> product-owner admin console — designed against the live backend API (FastAPI, Phases 0–6).
> **Companion docs:** `backend/README.md`, `backend/docs/*`, `backend/db/schema.sql`.

This is the single source of truth for what we build, how it looks and behaves, and how it
maps to the backend. It is written to Figma/Microsoft handoff standard: every page has a
purpose, layout, component inventory, data binding, and the full set of states (loading /
empty / error / partial / success). Nothing here is decorative — every screen ties to a real
endpoint or a clearly-flagged new one.

---

## Table of contents
1. Product vision & principles
2. Users, personas & jobs-to-be-done
3. Brand identity, logo & "real logos" policy
4. Design system — foundations (tokens)
5. Design system — components
6. Data-visualization system
7. Accessibility (WCAG 2.2 AA)
8. Responsive & layout system
9. UX writing, content & compliance
10. Information architecture & navigation
11. Global UX flows (auth, session, errors, degradation)
12. Page specifications — Marketing
13. Page specifications — Auth & onboarding
14. Page specifications — Core app
15. Page specifications — AI Advisor
16. Page specifications — Notifications & settings
17. Admin / product-owner console (+ required backend)
18. Front-end architecture (Next.js)
19. Data layer, types & API contract
20. Performance budget
21. Front-end security
22. Internationalization & money formatting
23. Analytics & instrumentation
24. Testing & quality gates
25. Design ops & Figma structure
26. Delivery roadmap & milestones
27. Definition of Done
28. Open decisions & assumptions
29. Appendix A — endpoint → screen matrix
30. Appendix B — route map

---

## 1. Product vision & principles

**Vision.** A calm, trustworthy financial copilot that turns a user's real bank data into
clear, grounded guidance — budgets, goals, debt payoff, portfolio health — with an AI advisor
that never invents numbers.

**Design principles** (decisions defer to these, in order):
1. **Trust before delight.** It holds people's money data. Security cues, accuracy, and
   honest empty/error states beat flourish.
2. **Grounded, never hallucinated.** Every figure is traceable to data; the AI shows its
   sources and degrades gracefully when unavailable.
3. **Clarity over density.** Money is stressful — one primary action per screen, progressive
   disclosure for depth.
4. **Accessible by default.** WCAG 2.2 AA is a gate, not a nicety. Finance must be usable by
   everyone.
5. **Fast on a mid-tier phone.** Core Web Vitals budget is a CI gate (§20).
6. **Consistent system, not one-off screens.** Everything is a token or a component.

---

## 2. Users, personas & jobs-to-be-done

| Persona | Context | Primary jobs | Tier likely |
|---|---|---|---|
| **Starter Sam** | early-career, one bank, anxious about overspend | "Am I okay this month?", set a first goal | Free |
| **Optimizer Olivia** | multiple accounts, some debt + investments | budget pacing, payoff strategy, rebalance | Plus |
| **Planner Priya** | household CFO, complex portfolio + goals | net-worth tracking, scenario what-ifs, advisor deep-dives | Premium |
| **Product Owner (you)** | runs the business | monitor health, manage users, control cost, audit | Admin |

**Tiers drive UI** (`users.tier` = `free | plus | premium`, token budgets 10k/100k/500k/day):
free sees upgrade nudges and a token meter; premium unlocks deeper advisor usage and
scenario tooling. Persona (`users.advisor_persona`, default `balanced`) tunes advisor tone and
is editable in Settings.

---

## 3. Brand identity, logo & "real logos" policy

**Working name: Fathom** — connotes depth + understanding ("I fathom my finances").
Alternates to consider: *Northstar, Ledgerly, Cair, Tideline*. **Locking the name is the one
blocking decision** (§28); everything else is name-agnostic via a `brand` token.

**Logo system (to be produced as SVG):**
- **Wordmark** — geometric humanist sans, custom "a" with a subtle depth notch.
- **Monogram** — an "F" formed from a depth/sonar arc; used as app icon, favicon, avatar.
- **Variants** — full color, mono (dark), mono (light), favicon 32/16, maskable PWA 512/192,
  social OG image.
- **Clear-space & min-size** rules documented in Figma.

**Brand palette** (finance-trust): deep navy `#0B1B2B`, emerald `#0E7C5A`, confident accent
`#3B82F6`, with semantic data colors in §4. Dark mode is first-class (default-respecting OS).

**Voice:** plain, calm, second-person, never hype. "You're $120 under budget" not "Crushing it!"

**"Real logos" policy (legitimate use only):**
- **Bank / institution logos** — render from **Plaid institution metadata** (`logo`,
  `primary_color`) on linked accounts and in the Link picker. These are provided for display.
- **Plaid trust mark** — show "Bank connections secured by Plaid" on the Link entry per Plaid's
  brand guidelines.
- **Security/trust badges** — 256-bit AES, SOC 2 (when achieved — do **not** claim early),
  bank-level encryption. Only claim what's true.
- **UI icon set** — **Lucide** (MIT) for interface icons; **simple-icons** (CC0) for any
  third-party brand glyphs (e.g., app-store badges) where licensing permits.
- **Never** use a bank/partner logo to imply endorsement or partnership we don't have.

---

## 4. Design system — foundations (tokens)

All values are **design tokens** (CSS variables + Tailwind theme + Figma variables), themed for
light/dark. Token names are stable contracts.

**Color — semantic (not raw):**
| Token | Light | Dark | Use |
|---|---|---|---|
| `bg/canvas` | `#F7F9FB` | `#0B1B2B` | page background |
| `bg/surface` | `#FFFFFF` | `#11263A` | cards |
| `bg/subtle` | `#EEF2F6` | `#16304A` | wells, hovers |
| `text/primary` | `#0B1B2B` | `#E8EEF4` | body |
| `text/secondary` | `#5A6B7B` | `#9DB0C2` | labels |
| `border/default` | `#E2E8F0` | `#244055` | dividers |
| `brand/primary` | `#0E7C5A` | `#16A37B` | primary actions |
| `accent/info` | `#3B82F6` | `#5B9DF8` | links, info |
| **Finance data colors** | | | **consistent meaning everywhere** |
| `data/positive` | `#0E7C5A` | gains, under-budget, income |
| `data/negative` | `#C2410C` | losses, over-budget, spend |
| `data/warning` | `#B45309` | approaching limits |
| `data/neutral` | `#64748B` | transfers, uncategorized |

> Money sign coloring is **semantic and fixed**: positive=emerald, negative=burnt-orange
> (not red/green — red/green fails common color blindness; pair with +/− glyphs and labels).

**Typography:** Inter (UI) + **tabular figures** for all money/numbers (`font-variant-numeric:
tabular-nums`). Scale (rem): 12, 14, 16(base), 18, 20, 24, 30, 36, 48. Weights 400/500/600/700.
Line-height 1.5 body, 1.2 headings.

**Spacing:** 4px base → 0,1(4),2(8),3(12),4(16),6(24),8(32),12(48),16(64). **Radius:** sm 6, md
10, lg 16, full. **Elevation:** 3 levels (card, popover, modal) + focus ring. **Z-index scale**
documented. **Motion:** durations 120/180/240ms, ease `cubic-bezier(.2,.8,.2,1)`; **all motion
respects `prefers-reduced-motion`** (swap to opacity-only/no transform).

---

## 5. Design system — components

Built on **shadcn/ui + Radix** (accessible primitives, fully owned). Every interactive
component must define **all states**: `default · hover · focus-visible · active · disabled ·
loading · error · empty`. Inventory:

**Primitives:** Button (primary/secondary/ghost/destructive/link), IconButton, Input, NumberInput,
**MoneyInput** (currency mask, enforces `0 < x ≤ 99,999,999.99` mirroring `MONEY_MAX`),
PercentInput, Select, **CategorySelect** (bound to the 14 `PLAID_CATEGORIES`), DatePicker
(future-only variant for goals), Checkbox, Radio, Switch, Slider, Textarea, Combobox, Tooltip,
Badge/Pill, Avatar, Skeleton, Spinner, Progress (bar + ring), Tabs, Accordion, Breadcrumb,
Pagination, Toast, Dialog/Modal, Drawer/Sheet, Popover, DropdownMenu, Command palette (⌘K),
EmptyState, ErrorState, Banner/Alert.

**Composite (product):**
- **MoneyAmount** — formatted, tabular, sign-colored, with screen-reader label
  ("negative $42.10").
- **StatCard** — KPI + delta + sparkline.
- **AccountCard** — bank logo, masked account, balance, sync status dot.
- **TransactionRow** — merchant, category chip, amount, date; swipe actions on mobile.
- **BudgetBar** — limit vs. spent, over-pace state.
- **GoalRing** — progress ring + monthly target + projected date.
- **DebtCard / PayoffTimeline / StrategyToggle** (snowball↔avalanche).
- **AllocationDonut / DriftBar / ConcentrationFlag.**
- **ChatMessage** (user/assistant), **ToolCallChip** (shows the advisor used a data tool),
  **SourceCitation**, **StreamingCursor**, **TokenBudgetMeter**.
- **NotificationItem**, **QuietHoursPicker**, **TimezoneSelect**.
- **PlaidLinkButton** (wraps Plaid Link SDK).
- **TierBadge / UpgradePrompt.**

**App shell:** TopBar (logo, ⌘K search, notifications bell, account menu), SideNav (desktop) /
BottomTab (mobile), PageHeader (title, actions, breadcrumbs), ContentGrid.

---

## 6. Data-visualization system

Charts (Recharts) follow one visual language: tabular-num axes, semantic data colors,
accessible (every chart has a data-table fallback + aria summary), responsive, animation-on-mount
only (reduced-motion aware).

| Chart | Where | Encoding |
|---|---|---|
| Sparkline | StatCards, dashboard | trend, no axis |
| Stacked bar | spend by category | category color map |
| Progress bar/ring | budgets, goals | pct fill, over-limit = `data/negative` |
| Line (area) | net worth, balances over time | positive/negative fill |
| Donut | portfolio allocation | asset-class palette |
| Diverging bar | rebalance drift | over/under target |
| Timeline | debt payoff months | milestone markers |

Rules: never use color alone to convey meaning (add labels/patterns); always show empty + loading
(skeleton) chart states; currency in tooltips uses the user's locale (§22).

---

## 7. Accessibility (WCAG 2.2 AA — gate)

- **Contrast** ≥ 4.5:1 text / 3:1 UI; verified per token pair.
- **Keyboard**: every action reachable; visible `focus-visible` ring; logical tab order;
  Esc closes overlays; ⌘K command palette; arrow-key menus (Radix).
- **Screen readers**: semantic landmarks, labeled forms, `aria-live` for toasts, advisor
  streaming, and balance updates; MoneyAmount announces sign + currency.
- **Forms**: errors tied via `aria-describedby`; never color-only; mirror backend
  `VALIDATION_ERROR` field locations.
- **Motion**: full `prefers-reduced-motion` support.
- **Targets**: ≥ 44×44px touch.
- **Testing**: axe in CI + manual NVDA/VoiceOver pass per release (§24).

---

## 8. Responsive & layout system

Mobile-first. Breakpoints: `sm 640 · md 768 · lg 1024 · xl 1280 · 2xl 1536`.
- **Mobile** (<768): bottom tab nav (Home, Money, Advisor, Alerts, Settings), single-column,
  sheets over modals, swipe actions.
- **Tablet** (768–1024): two-column, collapsible side nav.
- **Desktop** (≥1024): persistent side nav, multi-column dashboards, ⌘K, hover affordances.
- Max content width 1200px; 12-col grid, 24px gutters. Charts and tables reflow to cards on
  mobile. All money tables become stacked rows < md.

---

## 9. UX writing, content & compliance

- **Voice:** calm, factual, second person. Numbers do the talking.
- **Microcopy library** (in repo): buttons, empty states, errors, confirmations — all reviewed.
- **Error messages** map to the backend error contract (§11) but are humanized; never expose
  `request_id` to the user except in a "contact support" affordance.
- **Forgiving by default (user-friendly):** destructive actions (delete budget/goal, disconnect
  bank, mark-all-read) use either a **confirm dialog** (irreversible/high-stakes, e.g. disconnect
  bank which purges data) **or an optimistic action with a 5–8s "Undo" toast** (reversible, e.g.
  delete budget, mark read). Never both for the same action. Every form supports keyboard submit,
  preserves input on error, and autosaves drafts where sensible (advisor composer, long forms).
- **First-run friendliness:** every empty state teaches the next step with a sample/preview, not a
  dead end; onboarding is skippable and resumable; "why we ask" tooltips on anything that touches
  bank data.
- **Financial compliance copy (required):**
  - Persistent, unobtrusive disclaimer: *"Fathom provides educational information, not financial
    advice."* on advisor + planning surfaces.
  - The advisor's grounded/compliance framing from the backend validator is surfaced, not hidden.
  - **No buy/sell directives** in portfolio (the backend is data-only) — UI must not imply them.
  - TCPA: SMS opt-in is explicit, unchecked by default, with consent language.
  - CAN-SPAM: every marketing email has unsubscribe; transactional (verify) clearly separated.
- **Trust surfaces:** security page, data-handling explainer at Plaid Link, "why we ask" tooltips.

---

## 10. Information architecture & navigation

```
PUBLIC                     APP (auth + verified for money)         ADMIN (RBAC)
/                          /app (dashboard)                        /admin
/features                  /app/accounts                          /admin/users
/pricing                   /app/transactions                      /admin/ai
/security                  /app/budgets                           /admin/plaid
/about /legal/*            /app/goals                             /admin/notifications
/login /signup             /app/debt                              /admin/flags
/verify-email /resend      /app/portfolio                         /admin/audit
/reset-password            /app/advisor                           /admin/alerts
                           /app/notifications                     /admin/content
                           /app/settings/*                        /admin/settings
```
Primary nav (app): **Home · Accounts · Budgets · Goals · Debt · Portfolio · Advisor · Alerts ·
Settings**. Money-touching routes are gated on `is_verified` (else a verify-email interstitial).

---

## 11. Global UX flows (auth, session, errors, degradation)

**Auth/session model (matches backend):** access JWT held **in memory** (TanStack Query
client), refresh token is an **httpOnly cookie** set by `/auth/login`. A silent
`POST /auth/refresh` runs on 401 and on app focus; on refresh failure → route to `/login` with a
"session expired" toast. Never store tokens in `localStorage`.

**Standard error contract** → UI mapping (backend returns `{code, message, request_id,
details}`):
| Code | HTTP | UI treatment |
|---|---|---|
| `VALIDATION_ERROR` | 422 | inline field errors from `details[].loc` |
| `UNAUTHORIZED` | 401 | silent refresh → else login |
| `FORBIDDEN` | 403 | "no access" state; if unverified → verify interstitial |
| `CAPTCHA_REQUIRED` | 403 | render Turnstile, retry |
| `NOT_FOUND` | 404 | empty/not-found state |
| `CONFLICT` | 409 | inline ("already exists") |
| `RATE_LIMITED` | 429 | cool-down banner + Retry-After countdown |
| `PAYLOAD_TOO_LARGE` | 413 | form-level error |
| `AI_UNAVAILABLE` | 503 | advisor degradation banner (see below) |
| `SERVICE_BUSY` | 503 | "high demand, retry" toast + auto-retry w/ backoff |
| `PLAID_ERROR` | 502 | accounts error state + "reconnect bank" |
| `INTERNAL_ERROR` | 500 | generic error + "contact support" w/ request_id |

**AI degradation (`/health/ai` tiers 0/1/2):** tier 1 → subtle "advisor may be slower" note;
tier 2 / `AI_UNAVAILABLE` → banner "Advisor is temporarily unavailable — all other features work
normally," chat input disabled with retry. **Dashboards, budgets, goals never block on AI.**

**Offline / network loss:** global offline banner; queries show cached data with a "stale" hint;
mutations queue and replay on reconnect where safe (mark-read, etc.).

**Live updates (webhook-driven data).** Plaid syncs and alerts change data **server-side**; the
client reflects them without expensive constant polling:
- **Refetch-on-focus / on-visibility** (TanStack Query) — when the user returns to the tab or a
  screen, stale queries revalidate. Covers the vast majority of cases at near-zero idle cost.
- **Web Push** (service worker) for *delivered* notifications, so the bell updates without polling
  (see §20 — this is the 1M-scale notifications strategy).
- **Targeted invalidation** after user actions (link bank → invalidate accounts+dashboard).
- No always-on socket per user (would not scale to 1M idle connections); real-time is reserved for
  the advisor **stream** only, which is request-scoped.

**Global error boundary & app error pages.** A React error boundary wraps each route segment:
a render/runtime crash shows a recoverable "Something went wrong — reload" panel (never a white
screen), reports to monitoring with the `request_id` when present. Dedicated app pages: **404**
(not-found), **500** (app error), **403** (no access / unverified interstitial), **maintenance
mode** (driven by a feature flag / `/health` failure), and a **session-expired** redirect. Error
boundaries are per-segment so one broken widget never takes down the whole dashboard.

**Session-expiry at scale.** Silent refresh is **deduplicated** (a single in-flight refresh shared
across all queued 401s) so a burst of parallel requests triggers exactly one `/auth/refresh`, not
N — important when a tab wakes with many stale queries.

---

## 12. Page specifications — Marketing

For each: **purpose · layout · key components · CTA · SEO/states.**

- **/ (Landing)** — hero (product promise + app screenshot), trust strip (Plaid + security
  badges), feature highlights (advisor, budgets, debt, portfolio), social proof placeholder,
  pricing teaser, footer. SSR for SEO + OG image. CTA → signup.
- **/features** — deep dive per pillar with real UI imagery; each section maps to an app feature.
- **/pricing** — Free/Plus/Premium comparison (token budgets, advisor depth, scenario tools);
  monthly/annual toggle; FAQ. CTA → signup with tier preselected.
- **/security** — encryption (AES-256-GCM tokens), RLS tenant isolation explained simply,
  Plaid model, data deletion promise, responsible disclosure contact.
- **/about, /legal/{terms,privacy,disclosures}** — MDX content; the financial disclaimer lives
  in disclosures and globally.

States: all static-rendered; graceful no-JS; fast LCP (hero image priority-loaded).

---

## 13. Page specifications — Auth & onboarding

**Auth pages** (`/login`, `/signup`, `/verify-email`, `/resend`, `/reset-password`):
- **Signup** → `POST /auth/signup`. Fields: email, password (strength meter, mirrors
  min-length), optional name; Turnstile when `CAPTCHA_REQUIRED`. Success → "check your email."
- **Verify email** → `GET /auth/verify-email?token=` (deep link from email). States: verifying /
  success (→ login) / expired (→ resend CTA).
- **Resend** → `POST /auth/resend-verification` (captcha-gated). Always shows the generic
  anti-enumeration message regardless of account state.
- **Login** → `POST /auth/login`; sets refresh cookie. Step-up Turnstile after repeated fails;
  lockout → friendly `RATE_LIMITED` countdown. Generic "invalid email or password" (no
  enumeration).
- **Reset password** → *needs backend endpoints* (flagged §28). UI designed; gated on API.

**Onboarding wizard** (post-verify, driven by `users.onboarding_step`):
1. Welcome + persona pick (`advisor_persona`).
2. **Link first bank** (Plaid Link) — skippable, with "why we ask" + security copy.
3. Set a first goal (optional).
4. Done → dashboard. Progress saved per step; resumable.

---

## 14. Page specifications — Core app

### /app — Dashboard (Home)
- **Purpose:** "Am I okay?" at a glance.
- **Layout:** greeting + net-worth StatCard (area trend), row of StatCards (cash, this-month
  spend vs. budget, total debt, portfolio value), alerts strip (`/notifications` top 3), advisor
  nudge card, recent transactions.
- **Data:** budgets/goals/debt/portfolio summaries + notifications.
- **States:** **no bank linked** → prominent "Connect your bank" empty state with sample
  preview; loading → skeletons; partial (some modules empty) handled per-card; AI nudge hidden
  at degradation tier 2.

### /app/accounts — Accounts & connections
- **Purpose:** manage Plaid connections, see balances.
- **Flow:** `POST /plaid/link-token` → **Plaid Link** → `POST /plaid/exchange`; list via
  `GET /plaid/items`; disconnect via `DELETE /plaid/items/{id}` (confirm dialog — explains it
  revokes at Plaid + purges local data).
- **OAuth-bank redirect flow:** many large banks use Plaid's OAuth redirect. The app must:
  register a dedicated **`/app/accounts/oauth` redirect route** (matching the backend
  `plaid_redirect_uri`), persist the in-progress `link_token` so Link can be **re-initialized on
  return** with `receivedRedirectUri`, then continue to `/exchange`. Handle the user abandoning
  mid-OAuth (resume or restart cleanly).
- **Components:** AccountCard per item with **real bank logo**, masked number, balance, sync
  status (good / syncing / error → reconnect), institution color accent.
- **States:** empty (no items), linking (Link open), OAuth-return-resuming, syncing, item error
  (`PLAID_ERROR` → reconnect), revoke-confirm; live refresh on focus + push (§11).

### /app/transactions
- **Purpose:** browse/search/categorize spend.
- **Note:** *needs a dedicated `GET /transactions` (paginated, filterable) endpoint* — flagged
  §28 (today transactions are read only inside AI tools/dashboards).
- **Components:** virtualized list, search, filters (date range, account, category chip from
  `PLAID_CATEGORIES`), running totals, transfer exclusion indicator. Mobile: stacked rows + swipe.
- **States:** loading skeleton rows, empty, end-of-list, filter-no-match.

### /app/budgets
- **Purpose:** create/track category budgets.
- **CRUD:** `GET/POST /budgets`, `PATCH/DELETE /budgets/{id}`.
- **Components:** BudgetBar list (limit, spent, % used, remaining, over-pace warning), create
  sheet (CategorySelect from enum, **MoneyInput capped at MONEY_MAX**, alert-at-% 1–100).
- **Validation UX:** duplicate category → `CONFLICT` inline; over-cap amount → blocked client-side
  + 422 fallback; category must be one of the 14 (Select prevents free-text).
- **States:** empty (suggested starter budgets), at-limit, over-limit emphasis.

### /app/goals
- **Purpose:** savings goals with reverse-engineered monthly target.
- **CRUD:** `GET/POST /goals`, `PATCH/DELETE /goals/{id}`.
- **Components:** GoalRing cards (progress %, monthly target, projected date), create sheet
  (title, target amount ≤ MONEY_MAX, **future-only DatePicker**, current amount, priority).
- **Validation UX:** **past/today target date rejected** (DatePicker disables past; 422 fallback);
  contribute action updates `current_amount` → progress animates.
- **States:** empty, on-track / behind (`on_track` flag styling), completed celebration.

### /app/debt
- **Purpose:** payoff dashboard + strategy what-if.
- **Data:** `GET /debt` (summary, DTI, per-debt min, months-at-minimum, above-typical-rate
  flag), `POST /debt/payoff` (snowball vs. avalanche, with extra payment input ≤ MONEY_MAX).
- **Components:** DTI gauge, DebtCard list, **StrategyToggle** (snowball↔avalanche) with
  PayoffTimeline + interest-saved callout, refinance/ high-APR flags.
- **States:** **no debt linked** → positive empty state; feasibility warning when extra payment
  can't cover minimums.

### /app/portfolio
- **Purpose:** allocation, drift, concentration — **data only, no trade directives.**
- **Data:** `GET /portfolio` (total value, unrealized P/L, allocation %, sector exposure,
  concentration flags, top holdings), `POST /portfolio/rebalance` (target allocation → drift gaps).
- **Components:** AllocationDonut, sector bars, ConcentrationFlag chips, top-holdings table,
  rebalance planner (target % inputs summing ~100, DriftBar output).
- **Compliance:** explicit "informational, not a recommendation to buy/sell" note.
- **States:** no holdings empty state, single-holding concentration warning.

---

## 15. Page specifications — AI Advisor (`/app/advisor`)

- **Purpose:** grounded conversational guidance over the user's real data.
- **Data:** `POST /advisor/chat` (new turn, **streamed**), `GET /advisor/chats/{id}/messages`
  (history), `POST /advisor/messages/{id}/feedback` (👍/👎).
- **Layout:** chat thread, composer, conversation list (history), **TokenBudgetMeter** for tier
  (free 10k/day etc.), suggested prompts grounded in the user's state ("How's my budget?").
- **Streaming UX:** assistant message streams token-by-token (SSE/stream); **ToolCallChip**
  appears when the advisor calls a data tool ("Checked your budgets"); **SourceCitation** links the
  figures back to the relevant screen.
- **Safety/Compliance UX:** crisis/jailbreak inputs handled gracefully per backend safety layer;
  disclaimer persistent; the validator's grounding is surfaced (no raw unvalidated output).
- **States:** empty (welcome + prompts), streaming, tool-running, **budget exhausted** (upgrade
  prompt), **degradation/`AI_UNAVAILABLE`** (input disabled + banner; history still readable),
  `SERVICE_BUSY` auto-retry, feedback submitted confirmation.

---

## 16. Page specifications — Notifications & settings

### /app/notifications
- **Data:** `GET /notifications` (feed = alert rows, unread count), `POST /{id}/read`,
  `POST /read-all`.
- **Components:** NotificationItem list grouped by date, type icons (budget/goal/milestone/
  unusual-tx/bank-error), unread emphasis, mark-all. Bell in TopBar shows unread count, updated via
  **Web Push** + focus-refetch (no tight polling — see §20.2); feed fetched **on open**. Mark-read
  is **optimistic with undo**.
- **States:** empty, all-read, new-since-last-visit highlight, push-permission-prompt (soft ask).

### /app/settings/*
- **Profile** — name, email, persona (`advisor_persona`), tier badge (`/auth/me`).
- **Preferences** — `GET/PATCH /notifications/preferences`: per-type toggles, channel opt-ins
  (push/email/SMS), **QuietHoursPicker + TimezoneSelect**, **TCPA SMS opt-in** (explicit consent),
  weekly digest / monthly report toggles, marketing opt-in.
- **Security** — active sessions (needs list endpoint), logout-all, change password (needs
  endpoint), 2FA (future). Logout → `POST /auth/logout` clears refresh cookie.
- **Billing** — tier management; **needs Stripe integration** (§28). Display-only until then.
- **Data & privacy** — export, delete account (disconnects banks, purges data — maps to the
  cascade-on-disconnect behavior).

---

## 17. Admin / product-owner console (`/admin`)

> ⚠️ **Backend gap:** there are **no admin endpoints today**. The console UI is straightforward;
> each feature below names the **new backend** it requires. Recommend building read-only admin
> first (surfaces existing data), then write actions. RBAC roles: `owner · support · analyst`.

| Route | Owners do | New backend required |
|---|---|---|
| `/admin` | KPI dashboard: signups, DAU/MAU, linked-bank rate, AI usage/cost, alert volume, error rates | aggregate read APIs via audited `SECURITY DEFINER` views; reuse `/metrics` |
| `/admin/users` | search, view detail, verify/suspend, change tier, reset, **audited impersonation** | `/admin/users` list+detail+patch; suspend flag on `users`; impersonation token + audit |
| `/admin/ai` | live degradation tier, provider error rates, validation-failure rate, **per-day token spend + cost caps** | surface `/health/ai` + `/metrics`; token-spend query; spend-cap config |
| `/admin/plaid` | item health, failed syncs, webhook log, manual re-sync | `/admin/plaid/items`, sync-job status, re-sync trigger |
| `/admin/notifications` | edit email/push **templates**, view outbox, retry failed | template store + CRUD; outbox viewer + retry endpoint (outbox table exists) |
| `/admin/alerts` | alert-engine run history, dispatch counts, errors | run-history surfacing (engine exists) |
| `/admin/flags` | feature flags, edit **tier limits / token budgets** (today env constants) | flags + config table + API |
| `/admin/audit` | searchable security events (signup/login/link/admin actions) | `/admin/audit` query over existing `audit_logs` |
| `/admin/content` | manage pricing copy, FAQ, legal | CMS table or in-repo MDX |
| `/admin/settings` | admin roles/RBAC management | admin/roles table + role-checked middleware + admin JWT |

**Admin UX:** distinct chrome (denser, neutral theme) to avoid confusion with the user app;
every destructive/impersonation action is confirmed + audited + visible in `/admin/audit`.

---

## 18. Front-end architecture (Next.js)

```
frontend/
  app/
    (marketing)/            # public, statically rendered
    (auth)/                 # login, signup, verify, resend, reset
    (app)/                  # authenticated shell (layout guards verify)
      dashboard/ accounts/ transactions/ budgets/ goals/ debt/
      portfolio/ advisor/ notifications/ settings/
    (admin)/                # RBAC-guarded shell
    api/                    # route handlers (BFF: proxy refresh cookie, CSP nonce)
  components/  ui/ (shadcn)  charts/  product/  shell/
  lib/        api-client/   auth/  query/  format/  analytics/  flags/
  types/      generated from backend OpenAPI
  styles/     tokens.css (design tokens)  globals.css
  messages/   i18n catalogs
  tests/      unit/ component/ e2e(playwright)/ a11y/
  public/     brand/ (logos, favicons, OG)
```
- **Rendering:** marketing = static/SSR (SEO); app = client + RSC for fast reads; advisor uses
  streaming.
- **BFF route handlers** keep the refresh-cookie flow server-side and inject the CSP nonce.
- **Theming:** tokens drive Tailwind + Radix; dark mode via `class` strategy respecting OS.

---

## 19. Data layer, types & API contract

- **Type safety:** generate TS types + a typed client from the backend **OpenAPI** (`/openapi.json`)
  — `openapi-typescript` + a thin fetch wrapper. The API is the contract; no hand-written types
  drift.
- **Validation:** **Zod schemas mirror Pydantic** (MONEY_MAX, PLAID_CATEGORIES, future-date,
  email, password rules) so the client rejects before the round-trip and matches server 422s.
- **TanStack Query** conventions: query keys per resource, optimistic updates for budgets/goals/
  mark-read, automatic 401→refresh→retry, exponential backoff on `SERVICE_BUSY`, never retry
  `VALIDATION_ERROR`.
- **Error normalization:** one interceptor maps the `{code,…}` contract to typed UI errors (§11).

---

## 20. Performance & scale — built for 1M active users (CI gate)

### 20.1 Per-client performance budget
- **Core Web Vitals (field targets):** LCP < 2.5s, INP < 200ms, CLS < 0.1.
- **Dashboard p95 < 500ms** data render (backend target) — skeletons immediately, stream data in.
- **Bundle:** initial route JS < 180KB gz; route-level code splitting; charts lazy-loaded; advisor
  stream incremental; tree-shake icons; no moment/lodash-style heavyweights.
- **Images:** `next/image`, priority hero, bank logos cached/optimized; OG static.
- **Fonts:** `next/font` (Inter) self-hosted, `display: swap`.
- Lighthouse CI + bundle-size check in the pipeline; regressions fail the build.

### 20.2 Fleet-scale strategy (1M users) — *minimize backend load per user*
The frontend is a major lever on whether the backend survives 1M users. Principles:
- **Edge/CDN first.** Marketing = static + **ISR** (revalidate), served from CDN — zero origin
  hits for anonymous traffic. App shell + static assets fully CDN-cached and immutable-hashed.
- **No always-on sockets.** A persistent connection per user × 1M = a connection crisis. The only
  streaming is the **request-scoped advisor response**. Everything else is pull-on-demand.
- **Notifications without polling (the key scale decision).** A naive 30s bell poll = ~33k req/s
  at 1M users — unacceptable. Instead: **Web Push** (service worker) delivers notification *events*;
  the bell badge updates from push, and the feed is fetched **only when opened** or on tab focus.
  Fallback for no-push-permission: **adaptive long-interval poll** (e.g. 2–5 min, backed off when
  idle/hidden, paused when tab hidden) — not a tight loop.
- **Request coalescing & caching.** TanStack Query **dedupes** identical in-flight requests, caches
  with `staleTime` tuned per resource (dashboard summaries cache longer than a live balance), and
  **refetches on focus**, not on a timer. One shared silent-refresh for many 401s (§11).
- **Pagination & virtualization everywhere** large: transactions (keyset pagination + virtualized
  list), notifications, admin tables — never load unbounded sets.
- **Respect backend limits as signal, not error.** `429 RATE_LIMITED` → honor `Retry-After`;
  `503 SERVICE_BUSY` (the pool-shedding response) → exponential backoff + jitter, surfaced calmly —
  the client must **back off, not retry-storm**, or it amplifies an overload.
- **Prefetch judiciously.** Hover/intent prefetch for likely next routes; don't prefetch
  everything (wasted origin load at scale).

### 20.3 Safe delivery at scale
- **Feature flags + gradual rollout** (PostHog flags): ship behind a flag, ramp %; instant kill
  switch without a deploy — essential when a change hits 1M users.
- **Canary / staged deploys** on the edge; automatic rollback on CWV or error-rate regression.
- **Maintenance mode** flag (graceful read-only/parked state) driven by `/health`.
- **Resilience:** per-segment error boundaries (§11) isolate failures; offline cache keeps the app
  usable through blips; PWA installable for repeat users (faster, cached shell).

### 20.4 Capacity assumptions to validate with backend
- Steady-state read mix is dominated by dashboard + accounts + notifications; these must be
  **cache-friendly** (short `staleTime`, focus-refetch) so concurrent load stays bounded.
- Load-test the realistic journey with the existing **k6 script** (`backend/tests/load`) extended
  to include the notification-feed and accounts paths, asserting the p95 targets at projected
  concurrency before launch.

---

## 21. Front-end security

- **Tokens:** access JWT in memory only; refresh = httpOnly+Secure+SameSite cookie (backend-set).
  No secrets in the bundle.
- **CSP:** strict, nonce-based (`default-src 'none'`, explicit allowlist for Plaid + self); set
  via BFF — complements the backend hardening. No inline scripts.
- **XSS:** React escaping + sanitize any rendered markdown from the advisor; never `dangerouslySet`
  user/AI content unsanitized.
- **Clickjacking:** frame-ancestors none (backend already sends `X-Frame-Options: DENY`).
- **PII:** never log PII client-side; analytics events are property-allowlisted (§23).
- **Dependency hygiene:** `npm audit` + Dependabot, mirroring the backend `pip-audit` discipline.
- **Plaid:** load Link SDK from Plaid's domain only; never touch raw tokens (backend-only).

---

## 22. Internationalization & money formatting

- **next-intl** (or equivalent) with message catalogs; copy externalized from day one.
- **Money:** `Intl.NumberFormat` with the account/user currency (Plaid provides `currency_code`);
  tabular figures; never float-format — money strings come as decimals from the API and are parsed
  with a decimal-safe lib to avoid rounding drift.
- **Dates/numbers:** locale-aware; timezones honored (matches the notifications timezone pref).
- **RTL-ready:** logical CSS properties so RTL is a later flip, not a rewrite.
- **v1 ships en-US**; structure supports more without refactor.

---

## 23. Analytics & instrumentation

- **Privacy-first** product analytics (e.g., PostHog self-host or similar): event-based, no PII,
  consented.
- **Key funnels:** signup→verify→first-bank-link→first-budget/goal→first-advisor-chat;
  activation = linked bank + 1 plan object.
- **Events (allowlisted props):** `signup_started/completed`, `email_verified`,
  `bank_link_started/succeeded/failed`, `budget_created`, `goal_created`, `advisor_message_sent`,
  `advisor_feedback`, `upgrade_prompt_shown/clicked`, error occurrences by `code`.
- **Performance RUM:** Web Vitals reported. **Admin KPI dashboard consumes these + backend
  `/metrics`.**

---

## 24. Testing & quality gates

| Layer | Tool | Gate |
|---|---|---|
| Unit (lib/format/validation) | Vitest | required |
| Component | Testing Library + Storybook interaction | required |
| Visual regression | Storybook + Chromatic (or Playwright snapshots) | required on UI PRs |
| E2E flows | **Playwright** (signup→verify→link→budget→advisor) | required |
| Accessibility | axe (CI) + manual NVDA/VoiceOver per release | required |
| Type/lint | tsc strict + ESLint + Prettier | required |
| Perf | Lighthouse CI + bundle budget | required |
| Contract | OpenAPI types check against backend schema | required |

Mirrors the backend discipline (ruff/mypy/pytest must all be green).

---

## 25. Design ops & Figma structure

- **Figma file structure:** `00 Cover · 01 Foundations (tokens) · 02 Components (variants+states) ·
  03 Patterns · 04 Flows · 05 Screens (per feature) · 06 Prototypes · 07 Handoff`.
- **Figma Variables** = the design tokens in §4 (same names), kept in sync with `tokens.css` (one
  source of truth; tokens exported via Style Dictionary or Tokens Studio).
- **Component parity:** every coded component has a Figma counterpart with identical states.
- **Handoff:** redlines auto from variables; Storybook is the live mirror of production components.
- **Naming convention** shared across Figma + code (`Button/primary/lg`, `data/positive`).

---

## 26. Delivery roadmap & milestones

| Phase | Scope | Exit criteria |
|---|---|---|
| **F0 — Foundation** | Next.js scaffold, tokens, Tailwind+shadcn, brand logo, app shell, OpenAPI types, auth (login/signup/verify/resend) + session/refresh, error system | login→dashboard shell works; a11y + perf gates green |
| **F1 — Core money** | Accounts/Plaid Link, Dashboard, Budgets, Goals, onboarding wizard | a user can link a bank, set a budget+goal, see the dashboard |
| **F2 — Advanced** | Debt, Portfolio, Notifications + preferences, Settings | all user features live & tested |
| **F3 — AI Advisor** | streaming chat, tool chips, citations, token meter, degradation states | grounded chat end-to-end, feedback, graceful 503 |
| **F4 — Marketing** | landing, features, pricing, security, legal | SEO + CWV pass |
| **F5 — Admin console** | *with new backend APIs*: read-only KPIs/users/AI/audit → then write actions, RBAC | owners can monitor + manage |
| **F6 — Polish** | visual QA, full a11y audit, perf, content pass, i18n scaffolding | DoD met (§27) |

**Dependencies to unblock:** brand name lock (F0); `GET /transactions` (F1/F2); admin APIs +
RBAC (F5); password-reset + sessions-list + Stripe (Settings); live keys to exercise Plaid/AI for
real (cross-cutting).

---

## 27. Definition of Done (every feature)

- [ ] Matches Figma (component + states) and design tokens.
- [ ] All states implemented: loading, empty, error (mapped to backend contract), partial, success.
- [ ] Responsive across sm→2xl; mobile nav + touch targets.
- [ ] WCAG 2.2 AA: keyboard, SR labels, contrast, reduced-motion.
- [ ] Types generated from OpenAPI; Zod validation mirrors Pydantic.
- [ ] Money is decimal-safe, tabular, sign-semantic, locale-formatted.
- [ ] Optimistic/refresh/error handling via TanStack Query conventions.
- [ ] **Scale-safe:** no tight polling; refetch-on-focus; backs off (not retries) on 429/`SERVICE_BUSY`;
      large lists paginated + virtualized; behind a feature flag for staged rollout.
- [ ] **Resilient:** wrapped in a route-segment error boundary; reversible destructive actions have
      Undo, irreversible ones have a confirm dialog.
- [ ] Unit + component + (where a flow) e2e tests; axe clean.
- [ ] Perf budget met; no CLS from late data.
- [ ] Compliance copy present where required (disclaimer, no trade directives, TCPA/CAN-SPAM).
- [ ] Analytics events fired (allowlisted props, no PII).

---

## 28. Open decisions & assumptions

**Resolved** (see `frontend/ADMIN_CONSOLE_PLAN.md` for the full operational plan):
- ✅ **Admin console:** design-complete now, built as a **fast-follow (F5)** — user app ships
  first; admin backend + UI proceed in parallel from the §17/admin-plan contract.
- ✅ **Billing:** **display-only tiers at launch + Stripe-ready architecture**; real Stripe as the
  immediate billing fast-follow (Stripe Checkout + Customer Portal + signature-verified webhooks →
  `tier` sync).
- ✅ **Analytics:** **PostHog, self-hosted, consent-gated, zero PII**; feeds the admin KPI dashboard.

**Still needed from product owners:**
1. **Brand name** (Fathom provisional) + go-ahead to produce the logo set.
2. Admin identity model (separate `admins` table recommended), IP-allowlist, and session-replay
   choices — see ADMIN_CONSOLE_PLAN §14.

**Backend additions this plan assumes (each flagged at point of use):**
- `GET /transactions` (paginated/filterable) for the Transactions page.
- Password reset (`/auth/forgot`, `/auth/reset`) + active-sessions list/revoke.
- Full **admin API surface + RBAC** (§17).
- Stripe billing endpoints + webhook.
- Notification template store + outbox retry endpoint; feature-flags/config API.

**Assumptions:** Next.js/TS (per README); single currency (USD) at v1 with i18n scaffolding;
web-first (PWA-installable), native apps later; SOC 2 claimed only once achieved.

---

## 29. Appendix A — endpoint → screen matrix

| Backend endpoint | Screen(s) |
|---|---|
| `POST /auth/signup` | Signup |
| `GET /auth/verify-email` | Verify-email |
| `POST /auth/resend-verification` | Resend |
| `POST /auth/login` `POST /auth/refresh` `POST /auth/logout` | Login, global session |
| `GET /auth/me` | Settings/Profile, app shell |
| `POST /plaid/link-token` `POST /plaid/exchange` | Accounts, Onboarding |
| `GET /plaid/items` `DELETE /plaid/items/{id}` | Accounts |
| `POST /webhooks/plaid` | (server) → drives Accounts live refresh + alerts |
| `POST /advisor/chat` `GET /advisor/chats/{id}/messages` `POST /advisor/messages/{id}/feedback` | Advisor |
| `GET/POST /budgets` `PATCH/DELETE /budgets/{id}` | Budgets |
| `GET/POST /goals` `PATCH/DELETE /goals/{id}` | Goals |
| `GET /debt` `POST /debt/payoff` | Debt |
| `GET /portfolio` `POST /portfolio/rebalance` | Portfolio |
| `GET /notifications` `POST /{id}/read` `POST /read-all` | Notifications, bell |
| `GET/PATCH /notifications/preferences` | Settings/Preferences |
| `GET /health/ai` `GET /metrics` | Degradation UX, Admin/AI |
| *new:* `GET /transactions` | Transactions |
| *new:* admin APIs | Admin console |

## 30. Appendix B — route map

```
PUBLIC   /  /features  /pricing  /security  /about  /legal/{terms,privacy,disclosures}
AUTH     /login  /signup  /verify-email  /resend  /reset-password
APP      /app  /app/accounts  /app/transactions  /app/budgets  /app/goals
         /app/debt  /app/portfolio  /app/advisor  /app/notifications
         /app/settings/{profile,preferences,security,billing,privacy}
ADMIN    /admin  /admin/users  /admin/ai  /admin/plaid  /admin/notifications
         /admin/alerts  /admin/flags  /admin/audit  /admin/content  /admin/settings
```

---

*End of specification v1.0. Lock the brand name and the admin-scope decision (§28) and F0 can
begin immediately.*
