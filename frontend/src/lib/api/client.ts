"use client";

import { useMemo } from "react";
import { useAuth } from "@/lib/auth/context";
import type { ApiError } from "@/lib/auth/types";

/** Error carrying the backend's contract + HTTP status, for typed handling. */
export class ApiRequestError extends Error {
  constructor(
    public status: number,
    public payload: ApiError,
  ) {
    super(payload?.message || `Request failed (${status})`);
    this.name = "ApiRequestError";
  }
}

/**
 * Typed client bound to the authenticated BFF proxy (`/api/backend/*`). Adds the
 * in-memory access token via authedFetch, parses JSON, and throws
 * ApiRequestError on non-2xx so TanStack Query can branch on status/code.
 */
export function useApiClient() {
  const { authedFetch } = useAuth();

  return useMemo(() => {
    async function request<T>(path: string, init?: RequestInit): Promise<T> {
      const res = await authedFetch(path, init);
      const text = await res.text();
      const body = text ? JSON.parse(text) : null;
      if (!res.ok) throw new ApiRequestError(res.status, body as ApiError);
      return body as T;
    }
    return {
      get: <T,>(path: string) => request<T>(path),
      post: <T,>(path: string, data: unknown) =>
        request<T>(path, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(data),
        }),
      patch: <T,>(path: string, data: unknown) =>
        request<T>(path, {
          method: "PATCH",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(data),
        }),
      del: <T,>(path: string) => request<T>(path, { method: "DELETE" }),
    };
  }, [authedFetch]);
}
