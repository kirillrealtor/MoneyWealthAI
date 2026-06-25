"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useApiClient } from "./client";

export type PlaidAccount = {
  account_id: string;
  name: string | null;
  type: string | null;
  subtype: string | null;
  balance_current: string | null;
  currency_code: string | null;
};

export type PlaidItem = {
  item_id: string;
  institution_name: string | null;
  item_status: string;
  last_sync_at: string | null;
  accounts: PlaidAccount[];
};

const KEY = ["plaid", "items"] as const;

export function usePlaidItems() {
  const api = useApiClient();
  return useQuery({ queryKey: KEY, queryFn: () => api.get<PlaidItem[]>("/plaid/items") });
}

export function useCreateLinkToken() {
  const api = useApiClient();
  return useMutation({
    mutationFn: (environment: string) =>
      api.post<{ link_token: string; expiration?: string }>(`/plaid/link-token?environment=${environment}`, {}),
  });
}

export function useExchangeToken() {
  const api = useApiClient();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ public_token, environment }: { public_token: string; environment: string }) =>
      api.post<{ item_id: string; institution_name: string | null; accounts_linked: number }>(
        `/plaid/exchange?environment=${environment}`,
        { public_token },
      ),
    onSuccess: () => {
      // New bank linked → refresh everything that derives from accounts.
      qc.invalidateQueries({ queryKey: KEY });
      qc.invalidateQueries({ queryKey: ["debt"] });
      qc.invalidateQueries({ queryKey: ["portfolio"] });
      qc.invalidateQueries({ queryKey: ["budgets"] });
    },
  });
}

export function useDisconnectItem() {
  const api = useApiClient();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => api.del<{ message: string }>(`/plaid/items/${itemId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
