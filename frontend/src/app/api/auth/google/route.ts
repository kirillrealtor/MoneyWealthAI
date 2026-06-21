import { backendFetch } from "@/lib/server/backend";
import { setRefreshCookie } from "@/lib/server/session";

/** Continue with Google → forward the ID token to the backend, capture its
 *  refresh token as our first-party httpOnly cookie, return the access token. */
export async function POST(request: Request) {
  const payload = await request.text();
  const r = await backendFetch("/api/v1/auth/google", { method: "POST", body: payload });

  if (r.status === 200 && r.refreshToken) {
    await setRefreshCookie(r.refreshToken);
  }
  return Response.json(r.body, { status: r.status });
}
