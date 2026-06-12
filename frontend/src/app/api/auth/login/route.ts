import { backendFetch } from "@/lib/server/backend";
import { setRefreshCookie } from "@/lib/server/session";

/** Proxy login → backend, capture its refresh token as our first-party httpOnly
 *  cookie, and return only the access token (held in client memory). */
export async function POST(request: Request) {
  const payload = await request.text();
  const r = await backendFetch("/api/v1/auth/login", { method: "POST", body: payload });

  if (r.status === 200 && r.refreshToken) {
    await setRefreshCookie(r.refreshToken);
  }
  // Strip nothing sensitive: body is { access_token, user_id } on success.
  return Response.json(r.body, { status: r.status });
}
