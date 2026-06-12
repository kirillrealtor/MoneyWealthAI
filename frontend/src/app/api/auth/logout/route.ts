import { backendFetch } from "@/lib/server/backend";
import { getRefreshCookie, clearRefreshCookie } from "@/lib/server/session";

/** Revoke the session at the backend and drop the first-party cookie. */
export async function POST() {
  const rt = await getRefreshCookie();
  if (rt) {
    await backendFetch("/api/v1/auth/logout", {
      method: "POST",
      headers: { cookie: `refresh_token=${encodeURIComponent(rt)}` },
    });
  }
  await clearRefreshCookie();
  return Response.json({ ok: true });
}
