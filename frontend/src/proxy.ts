import { NextResponse, type NextRequest } from "next/server";

/**
 * Per-request Content-Security-Policy with a fresh nonce (Next 16 `proxy`,
 * formerly `middleware`). This is the primary XSS guard for a fintech app:
 *
 *  - script-src: 'self' + per-request nonce + 'strict-dynamic' → only our own
 *    nonced scripts run; injected <script> tags are blocked. Next applies the
 *    nonce to its own hydration scripts automatically when it sees this header.
 *  - style-src allows 'unsafe-inline' because React emits inline `style`
 *    attributes (nonces don't apply to style attributes); style injection is
 *    far lower risk than script injection.
 *  - frame-ancestors 'none' blocks clickjacking; object-src 'none' kills plugins;
 *    base-uri/form-action 'self' stop base-tag and form-hijack tricks.
 *  - frame-src allows Plaid Link (bank connect) for when accounts ship.
 *  'unsafe-eval' is dev-only (React Refresh / Turbopack); never in production.
 */
export function proxy(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const isDev = process.env.NODE_ENV === "development";

  const csp = [
    "default-src 'self'",
    // cdn.plaid.com is a CSP2 fallback (ignored under strict-dynamic, where the
    // nonced Plaid Link bundle loads it via trust propagation).
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic' https://cdn.plaid.com${isDev ? " 'unsafe-eval'" : ""}`,
    "style-src 'self' 'unsafe-inline' https://accounts.google.com",
    "img-src 'self' blob: data: https:",
    "font-src 'self'",
    "connect-src 'self' https://*.plaid.com https://accounts.google.com",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "frame-src 'self' https://*.plaid.com https://accounts.google.com",
    "worker-src 'self' blob:",
    "manifest-src 'self'",
    ...(isDev ? [] : ["upgrade-insecure-requests"]),
  ].join("; ");

  // Pass the nonce to the app (server components read it via headers()).
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("content-security-policy", csp);

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", csp);
  return response;
}

export const config = {
  matcher: [
    // Run on all routes except static assets / image optimizer / favicon, and
    // skip prefetch requests (no need to pay for CSP generation on those).
    {
      source: "/((?!_next/static|_next/image|favicon.ico).*)",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
  ],
};
