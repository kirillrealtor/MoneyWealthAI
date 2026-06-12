import { backendFetch } from "@/lib/server/backend";

/** Proxy signup. No cookie is set — the user must verify their email, then log in. */
export async function POST(request: Request) {
  const payload = await request.text();
  const r = await backendFetch("/api/v1/auth/signup", { method: "POST", body: payload });
  return Response.json(r.body, { status: r.status });
}
