import "server-only";

/**
 * Server-only backend client (the BFF's outbound half). The browser NEVER talks
 * to the backend directly — only Next route handlers do, here. `API_BASE_URL` is
 * a server-only env var (no NEXT_PUBLIC_ prefix), so the backend origin and any
 * forwarded credentials never reach the client bundle.
 */
const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:3000";

export type BackendResult = {
  status: number;
  body: unknown;
  /** Raw refresh-token value lifted from the backend's Set-Cookie, if present. */
  refreshToken?: string;
};

const REFRESH_COOKIE_NAME = "refresh_token"; // backend's cookie name

/** Call the backend API. Returns parsed JSON + status; never throws on 4xx/5xx. */
export async function backendFetch(
  path: string,
  init: RequestInit & { bearer?: string; tenantId?: string } = {},
): Promise<BackendResult> {
  const { bearer, tenantId, headers, ...rest } = init;
  const h = new Headers(headers);
  h.set("content-type", "application/json");
  h.set("accept", "application/json");
  if (bearer) h.set("authorization", `Bearer ${bearer}`);
  if (tenantId) h.set("x-tenant-id", tenantId);

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...rest,
      headers: h,
      cache: "no-store",
      redirect: "manual",
    });
  } catch {
    return { status: 502, body: { code: "PLAID_ERROR", message: "Upstream unavailable." } };
  }

  const refreshToken = extractRefreshToken(res.headers);
  let body: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = { raw: text };
    }
  }
  return { status: res.status, body, refreshToken };
}

/** Pull the refresh-token value out of a backend Set-Cookie header. */
function extractRefreshToken(headers: Headers): string | undefined {
  // Next/undici exposes getSetCookie() for multiple Set-Cookie headers.
  const all =
    typeof headers.getSetCookie === "function"
      ? headers.getSetCookie()
      : [headers.get("set-cookie") ?? ""];
  for (const c of all) {
    const m = c.match(new RegExp(`${REFRESH_COOKIE_NAME}=([^;]+)`));
    if (m) return decodeURIComponent(m[1]);
  }
  return undefined;
}
