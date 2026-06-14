"use client";

import { createContext, useCallback, useContext, useRef, useState } from "react";
import type { ApiError } from "@/lib/auth/types";

type AdminStatus = "unauthenticated" | "authenticated";
type LoginResult = { ok: true } | { ok: false; error: ApiError };

type AdminContextValue = {
  role: string | null;
  status: AdminStatus;
  login: (email: string, password: string) => Promise<LoginResult>;
  logout: () => void;
  /** Authenticated admin fetch via the BFF proxy (/api/backend/admin<path>). */
  adminFetch: (path: string, init?: RequestInit) => Promise<Response>;
};

const AdminContext = createContext<AdminContextValue | null>(null);

export function AdminProvider({ children }: { children: React.ReactNode }) {
  const [role, setRole] = useState<string | null>(null);
  const [status, setStatus] = useState<AdminStatus>("unauthenticated");
  // Admin access token: in memory only, short-lived (30 min). No persistence —
  // a page refresh requires re-login (intentional for a high-privilege console).
  const token = useRef<string | null>(null);

  const login = useCallback<AdminContextValue["login"]>(async (email, password) => {
    const res = await fetch("/api/backend/admin/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) return { ok: false, error: data as ApiError };
    token.current = (data as { access_token: string }).access_token;
    setRole((data as { role: string }).role);
    setStatus("authenticated");
    return { ok: true };
  }, []);

  const logout = useCallback(() => {
    token.current = null;
    setRole(null);
    setStatus("unauthenticated");
  }, []);

  const adminFetch = useCallback<AdminContextValue["adminFetch"]>(async (path, init = {}) => {
    const res = await fetch(`/api/backend/admin${path}`, {
      ...init,
      headers: {
        ...(init.headers ?? {}),
        ...(token.current ? { authorization: `Bearer ${token.current}` } : {}),
      },
    });
    if (res.status === 401) {
      // Token expired / missing → drop session so the shell routes to login.
      token.current = null;
      setRole(null);
      setStatus("unauthenticated");
    }
    return res;
  }, []);

  return (
    <AdminContext.Provider value={{ role, status, login, logout, adminFetch }}>
      {children}
    </AdminContext.Provider>
  );
}

export function useAdmin() {
  const ctx = useContext(AdminContext);
  if (!ctx) throw new Error("useAdmin must be used within <AdminProvider>");
  return ctx;
}
