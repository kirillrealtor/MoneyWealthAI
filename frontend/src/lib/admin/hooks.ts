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

export type AiOps = {
  stats: {
    tier: number;
    calls_total: number;
    errors_total: number;
    error_rate: number;
    tokens_total: number;
    validation_failures: number;
    by_provider: Record<string, number>;
  };
  usage: { day: string; tokens: number; users: number }[];
  top_users: { user_id: string; email: string; tokens: number }[];
  tier_budgets: { free: number; plus: number; premium: number };
};

export type PlaidOps = {
  health: {
    total_items: number;
    good_items: number;
    error_items: number;
    active_jobs: number;
    failed_jobs_24h: number;
  };
  jobs: {
    sync_id: string;
    item_id: string;
    status: string;
    error_message: string | null;
    transactions_synced: number;
    started_at: string;
  }[];
};

export function useAiOps() {
  const get = useGet();
  return useQuery({ queryKey: ["admin", "ai"], queryFn: () => get<AiOps>("/ai"), refetchInterval: 30_000 });
}

export function usePlaidOps() {
  const get = useGet();
  return useQuery({ queryKey: ["admin", "plaid"], queryFn: () => get<PlaidOps>("/plaid"), refetchInterval: 30_000 });
}

export function useResync() {
  const { adminFetch } = useAdmin();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (itemId: string) => {
      const res = await adminFetch(`/plaid/items/${itemId}/resync`, { method: "POST" });
      if (!res.ok) throw new Error("resync failed");
      return res.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "plaid"] }),
  });
}

export type OutboxRow = {
  outbox_id: string;
  channel: string;
  status: string;
  attempts: number;
  error: string | null;
  created_at: string;
  sent_at: string | null;
};

export function useOutbox(status: string) {
  const get = useGet();
  return useQuery({
    queryKey: ["admin", "outbox", status],
    queryFn: () => get<{ items: OutboxRow[] }>(`/outbox${status ? `?status=${status}` : ""}`),
    refetchInterval: 30_000,
  });
}

export function useRetryOutbox() {
  const { adminFetch } = useAdmin();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await adminFetch(`/outbox/${id}/retry`, { method: "POST" });
      if (!res.ok) throw new Error("retry failed");
      return res.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "outbox"] }),
  });
}

export type Flag = { key: string; enabled: boolean; description: string | null; updated_at: string };

export function useFlags() {
  const get = useGet();
  return useQuery({ queryKey: ["admin", "flags"], queryFn: () => get<Flag[]>("/flags") });
}

export function useSetFlag() {
  const { adminFetch } = useAdmin();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ key, enabled }: { key: string; enabled: boolean }) => {
      const res = await adminFetch(`/flags/${key}`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ enabled }),
      });
      if (!res.ok) throw new Error("flag update failed");
      return res.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "flags"] }),
  });
}

export function useAudit(limit = 50, offset = 0) {
  const get = useGet();
  return useQuery({
    queryKey: ["admin", "audit", limit, offset],
    queryFn: () => get<{ items: AuditRow[]; limit: number; offset: number }>(`/audit?limit=${limit}&offset=${offset}`),
  });
}
