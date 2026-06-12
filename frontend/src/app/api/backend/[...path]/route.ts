import { backendFetch } from "@/lib/server/backend";

/**
 * Authenticated BFF proxy for all non-auth backend calls (me, budgets, goals…).
 * The browser sends its in-memory access token as `Authorization: Bearer …`;
 * we forward only safe headers to the fixed backend base — so the backend origin
 * stays server-side and there's no open-redirect/SSRF (path is appended to a
 * constant base, never a full URL).
 */
async function forward(request: Request, path: string[]) {
  const url = new URL(request.url);
  const target = `/api/v1/${path.map(encodeURIComponent).join("/")}${url.search}`;

  const auth = request.headers.get("authorization") ?? undefined;
  const bearer = auth?.startsWith("Bearer ") ? auth.slice(7) : undefined;
  const tenantId = request.headers.get("x-tenant-id") ?? undefined;
  const method = request.method;
  const body = method === "GET" || method === "HEAD" ? undefined : await request.text();

  const r = await backendFetch(target, { method, body, bearer, tenantId });
  return Response.json(r.body, { status: r.status });
}

type Ctx = { params: Promise<{ path: string[] }> };

export async function GET(request: Request, { params }: Ctx) {
  return forward(request, (await params).path);
}
export async function POST(request: Request, { params }: Ctx) {
  return forward(request, (await params).path);
}
export async function PATCH(request: Request, { params }: Ctx) {
  return forward(request, (await params).path);
}
export async function PUT(request: Request, { params }: Ctx) {
  return forward(request, (await params).path);
}
export async function DELETE(request: Request, { params }: Ctx) {
  return forward(request, (await params).path);
}
