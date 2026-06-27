import { backendFetch } from "@/lib/server/backend";

/** Proxy magic-link request → backend. No cookie is set until the user clicks the link. */
export async function POST(request: Request) {
  const payload = await request.text();
  const r = await backendFetch("/api/v1/auth/magic-link", { method: "POST", body: payload });
  return Response.json(r.body, { status: r.status });
}
