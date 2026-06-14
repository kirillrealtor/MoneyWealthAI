"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAdmin } from "./context";

export type Kpis = {
  total_users: number;
  verified_users: number;
  suspended_users: number;
  signups_today: number;
  signups_7d: number;
  signups_30d: number;
  total_budgets: number;
  total_goals: number;
  linked_items: number;
};

export type AdminUserRow = {
  user_id: string;
  email: string;
  full_name: string | null;
  tier: string;
  is_verified: boolean;
  suspended: boolean;
  created_at: string;
  last_login_at: string | null;
};

export type AdminUserDetail = AdminUserRow & {
  advisor_persona: string;
  onboarding_step: number;
  budget_count: number;
  goal_count: number;
  linked_items: number;
};

export type AuditRow = {
  log_id: string;
  user_id: string | null;
  action: string;
  resource: string | null;
  resource_id: string | null;
  ip_address: string | null;
  ts: string;
};

/** Thin helper: adminFetch + JSON parse + throw on non-2xx. */
function useGet() {
  const { adminFetch } = useAdmin();
  return async <T,>(path: string): Promise<T> => {
    const res = await adminFetch(path);
    const body = await res.json();
    if (!res.ok) throw Object.assign(new Error("request failed"), { status: res.status, body });
    return body as T;
  };
}

export function useKpis() {
  const get = useGet();
  return useQuery({ queryKey: ["admin", "kpis"], queryFn: () => get<Kpis>("/metrics") });
}

export function useAdminUsers(search: string, limit = 25, offset = 0) {
  const get = useGet();
  return useQuery({
    queryKey: ["admin", "users", search, limit, offset],
    queryFn: () => get<{ items: AdminUserRow[]; limit: number; offset: number }>(
      `/users?search=${encodeURIComponent(search)}&limit=${limit}&offset=${offset}`,
    ),
  });
}

export function useAdminUser(id: string) {
  const get = useGet();
  return useQuery({ queryKey: ["admin", "user", id], queryFn: () => get<AdminUserDetail>(`/users/${id}`) });
}

export function useUpdateUser(id: string) {
  const { adminFetch } = useAdmin();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (patch: { tier?: string; suspended?: boolean; is_verified?: boolean; reason?: string }) => {
      const res = await adminFetch(`/users/${id}`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(patch),
      });
      const body = await res.json();
      if (!res.ok) throw Object.assign(new Error("update failed"), { status: res.status, body });
      return body as AdminUserDetail;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "user", id] });
      qc.invalidateQueries({ queryKey: ["admin", "users"] });
      qc.invalidateQueries({ queryKey: ["admin", "kpis"] });
    },
  });
}

export function useAudit(limit = 50, offset = 0) {
  const get = useGet();
  return useQuery({
    queryKey: ["admin", "audit", limit, offset],
    queryFn: () => get<{ items: AuditRow[]; limit: number; offset: number }>(`/audit?limit=${limit}&offset=${offset}`),
  });
}
