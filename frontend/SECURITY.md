# Frontend Security Posture — Fathom

A fintech UI holds financial data. This documents the front-end security model so
it survives refactors. It complements the backend hardening (RLS, AES-GCM tokens,
rate limiting, pentest fixes) — see `backend/docs/SECURITY.md`.

## Threat model (what we defend against)
- **XSS / script injection** — the top web threat; an injected script could read
  the in-memory access token or exfiltrate on-screen financial data.
- **Token theft** — access/refresh tokens must never be reachable by injected JS.
- **Clickjacking** — a finance UI framed by an attacker to trick clicks.
- **Secret leakage into the client bundle** — the #1 frontend data-leak vector.
- **Sensitive data in URLs / logs / referrers.**

## Controls in place

### 1. HTTP security headers (`next.config.ts`)
`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
`Referrer-Policy: no-referrer`, `Strict-Transport-Security` (2y, preload),
`Permissions-Policy` (camera/mic/geo/payment/usb off), `Cross-Origin-Opener-Policy`
and `Cross-Origin-Resource-Policy: same-origin`, `X-DNS-Prefetch-Control: off`,
`X-Permitted-Cross-Domain-Policies: none`. `X-Powered-By` is **disabled**.

### 2. Strict, nonce-based CSP (`src/proxy.ts`)
Per-request nonce; `script-src 'self' 'nonce-…' 'strict-dynamic'` — only our own
nonced scripts run, injected `<script>` is blocked. `object-src 'none'`,
`base-uri 'self'`, `form-action 'self'`, `frame-ancestors 'none'`. `'unsafe-eval'`
is **dev-only**. This is the primary XSS guard.

### 3. Token handling (when auth ships)
- **Access token: in memory only** (never `localStorage`/`sessionStorage`, never a
  non-httpOnly cookie). An XSS that does run still can't read it from storage.
- **Refresh token: httpOnly + Secure + SameSite cookie**, set by the backend —
  unreadable by JS by design.
- Tokens are never put in URLs, query strings, or logs.

### 4. BFF data boundary (no secret leakage)
The browser talks only to this Next app (same origin). Next **server-side** route
handlers call the backend. Therefore:
- `API_BASE_URL` and all secrets are **server-only** (no `NEXT_PUBLIC_` prefix).
- Only values *designed* to be public (Stripe/Plaid publishable, Turnstile site
  key) may be `NEXT_PUBLIC_`. **Secret keys are never `NEXT_PUBLIC_`.**
- CI/lint rule (planned): fail the build if a secret-looking var is `NEXT_PUBLIC_`.

### 5. Output safety
- React escapes by default. **No `dangerouslySetInnerHTML`** for user/AI content;
  any markdown from the advisor is sanitized before render.
- The standardized backend error contract (`{code,message,request_id}`) is shown
  humanized; `request_id` is only surfaced in a "contact support" affordance.

### 6. Privacy
- Fonts are self-hosted via `next/font` (no third-party font CDN calls).
- No PII in analytics events; analytics are consent-gated (see plan §23).

## Verifying
```bash
# headers present (run against the dev/prod server)
curl -sI http://localhost:3100/ | grep -iE 'content-security-policy|x-frame|x-content-type|referrer|strict-transport|permissions-policy|x-powered-by'
# expect: CSP with a nonce, DENY, nosniff, no-referrer, HSTS, Permissions-Policy
# expect: NO x-powered-by line
```

## Non-goals / future
- CSP `connect-src`/`frame-src` will be tightened to exact Plaid/Stripe origins
  when those integrations ship (Plaid Link iframe is already allowed).
- `npm audit` + Dependabot gate in CI (mirrors backend `pip-audit`).
