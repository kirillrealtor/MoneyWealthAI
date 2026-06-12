"use client";

import { useQuery } from "@tanstack/react-query";
import { useApiClient } from "./client";
import type { DebtSummary, PayoffComparison, PortfolioSummary } from "./types";
import { useMutation } from "@tanstack/react-query";

export function useDebt() {
  const api = useApiClient();
  return useQuery({ queryKey: ["debt"], queryFn: () => api.get<DebtSummary>("/debt") });
}

export function usePayoff() {
  const api = useApiClient();
  return useMutation({
    mutationFn: (extra: string) =>
      api.post<PayoffComparison>("/debt/payoff", { extra_monthly_payment: extra }),
  });
}

export function usePortfolio() {
  const api = useApiClient();
  return useQuery({ queryKey: ["portfolio"], queryFn: () => api.get<PortfolioSummary>("/portfolio") });
}
