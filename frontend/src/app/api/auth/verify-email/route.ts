import { backendFetch } from "@/lib/server/backend";
import { setRefreshCookie } from "@/lib/server/session";

/** Proxy the email-verification token check (backend uses GET ?token=).
 *  Verification also logs the user in, so capture the refresh token as our
 *  first-party httpOnly cookie and return the access token (auto-login). */
export async function GET(request: Request) {
  const token = new URL(request.url).searchParams.get("token") ?? "";
  const r = await backendFetch(
    `/api/v1/auth/verify-email?token=${encodeURIComponent(token)}`,
    { method: "GET" },
  );
  if (r.status === 200 && r.refreshToken) {
    await setRefreshCookie(r.refreshToken);
  }
  return Response.json(r.body, { status: r.status });
}
