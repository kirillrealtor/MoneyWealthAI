"use client";

import { useQuery } from "@tanstack/react-query";
import { useApiClient } from "./client";

export type Transaction = {
  transaction_id: string;
  date: string;
  merchant_name: string | null;
  amount: string; // Plaid: positive = money out (spend)
  category: string | null;
  pending: boolean;
  currency_code: string;
};

export type TransactionList = { items: Transaction[]; limit: number; offset: number };

export function useTransactions(opts: { category?: string; search?: string; limit?: number; offset?: number }) {
  const api = useApiClient();
  const { category = "", search = "", limit = 50, offset = 0 } = opts;
  const qs = new URLSearchParams();
  if (category) qs.set("category", category);
  if (search) qs.set("search", search);
  qs.set("limit", String(limit));
  qs.set("offset", String(offset));
  return useQuery({
    queryKey: ["transactions", category, search, limit, offset],
    queryFn: () => api.get<TransactionList>(`/transactions?${qs.toString()}`),
  });
}
