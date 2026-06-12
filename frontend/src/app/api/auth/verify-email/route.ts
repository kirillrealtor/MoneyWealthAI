import { backendFetch } from "@/lib/server/backend";

/** Proxy the email-verification token check (backend uses GET ?token=). */
export async function GET(request: Request) {
  const token = new URL(request.url).searchParams.get("token") ?? "";
  const r = await backendFetch(
    `/api/v1/auth/verify-email?token=${encodeURIComponent(token)}`,
    { method: "GET" },
  );
  return Response.json(r.body, { status: r.status });
}
