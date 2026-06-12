"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useApiClient } from "./client";
import type { Goal } from "./types";

const KEY = ["goals"] as const;

export function useGoals() {
  const api = useApiClient();
  return useQuery({ queryKey: KEY, queryFn: () => api.get<Goal[]>("/goals") });
}

export type GoalInput = {
  title: string;
  target_amount: string;
  target_date: string;
  current_amount?: string;
  description?: string;
  priority?: number;
};

export function useCreateGoal() {
  const api = useApiClient();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: GoalInput) => api.post<Goal>("/goals", input),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useUpdateGoal() {
  const api = useApiClient();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...input }: { id: string } & Partial<GoalInput> & { status?: string }) =>
      api.patch<Goal>(`/goals/${id}`, input),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useDeleteGoal() {
  const api = useApiClient();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.del<{ message: string }>(`/goals/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
