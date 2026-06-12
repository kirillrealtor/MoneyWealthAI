"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useApiClient } from "./client";
import type { NotificationList, Preferences } from "./types";

const FEED = ["notifications"] as const;
const PREFS = ["preferences"] as const;

export function useNotifications() {
  const api = useApiClient();
  return useQuery({ queryKey: FEED, queryFn: () => api.get<NotificationList>("/notifications") });
}

export function useMarkRead() {
  const api = useApiClient();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.post<unknown>(`/notifications/${id}/read`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: FEED }),
  });
}

export function useMarkAllRead() {
  const api = useApiClient();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<unknown>("/notifications/read-all", {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: FEED }),
  });
}

export function usePreferences() {
  const api = useApiClient();
  return useQuery({ queryKey: PREFS, queryFn: () => api.get<Preferences>("/notifications/preferences") });
}

export function useUpdatePreferences() {
  const api = useApiClient();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch: Partial<Preferences>) =>
      api.patch<Preferences>("/notifications/preferences", patch),
    onSuccess: (data) => qc.setQueryData(PREFS, data),
  });
}
