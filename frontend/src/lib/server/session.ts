import "server-only";
import { cookies } from "next/headers";

/**
 * First-party refresh cookie. The backend hands us a refresh token (in its own
 * Set-Cookie); we re-issue it as OUR httpOnly cookie so the browser stores it
 * for the Next origin only. It is httpOnly (XSS can't read it), Secure in prod,
 * SameSite=Lax, and scoped to /api/auth so it's only sent to the refresh/logout
 * handlers. The access token is never stored — it lives in client memory.
 */
export const RT_COOKIE = "mw_rt";
const THIRTY_DAYS = 60 * 60 * 24 * 30;

export async function setRefreshCookie(token: string) {
  (await cookies()).set(RT_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/api/auth",
    maxAge: THIRTY_DAYS,
  });
}

export async function getRefreshCookie(): Promise<string | undefined> {
  return (await cookies()).get(RT_COOKIE)?.value;
}

export async function clearRefreshCookie() {
  (await cookies()).delete({ name: RT_COOKIE, path: "/api/auth" });
}
