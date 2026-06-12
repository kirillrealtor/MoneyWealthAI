import { backendFetch } from "@/lib/server/backend";

export async function POST(request: Request) {
  const payload = await request.text();
  const r = await backendFetch("/api/v1/auth/resend-verification", {
    method: "POST",
    body: payload,
  });
  return Response.json(r.body, { status: r.status });
}
