"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useApiClient } from "./client";

export type Subscription = {
  tier: string;
  status: string;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
} | null;

export function useSubscription() {
  const api = useApiClient();
  return useQuery({ queryKey: ["billing", "subscription"], queryFn: () => api.get<Subscription>("/billing/subscription") });
}

/** Start Stripe Checkout for a plan, then redirect the browser to it. */
export function useStartCheckout() {
  const api = useApiClient();
  return useMutation({
    mutationFn: (input: { plan: "plus" | "premium"; interval: "monthly" | "annual" }) =>
      api.post<{ url: string }>("/billing/checkout", input),
    onSuccess: ({ url }) => {
      window.location.assign(url);
    },
  });
}

/** Open the Stripe Customer Portal (manage / cancel), then redirect. */
export function useOpenPortal() {
  const api = useApiClient();
  return useMutation({
    mutationFn: () => api.post<{ url: string }>("/billing/portal", {}),
    onSuccess: ({ url }) => {
      window.location.assign(url);
    },
  });
}
