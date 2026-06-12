"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useApiClient } from "./client";
import type { Budget } from "./types";

const KEY = ["budgets"] as const;

export function useBudgets() {
  const api = useApiClient();
  return useQuery({ queryKey: KEY, queryFn: () => api.get<Budget[]>("/budgets") });
}

export type BudgetInput = { category: string; monthly_limit: string; alert_at_pct?: number };

export function useCreateBudget() {
  const api = useApiClient();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: BudgetInput) => api.post<Budget>("/budgets", input),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useUpdateBudget() {
  const api = useApiClient();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...input }: { id: string } & Partial<BudgetInput> & { is_active?: boolean }) =>
      api.patch<Budget>(`/budgets/${id}`, input),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useDeleteBudget() {
  const api = useApiClient();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.del<{ message: string }>(`/budgets/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
