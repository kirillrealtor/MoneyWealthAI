"use client";

import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { AuthProvider } from "@/lib/auth/context";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: true, // live-ish without polling (see plan §20)
            retry: (count, err) => {
              // Don't retry validation/auth; back off briefly otherwise.
              const status = (err as { status?: number })?.status;
              if (status && status < 500 && status !== 503) return false;
              return count < 2;
            },
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={client}>
      <AuthProvider>{children}</AuthProvider>
      <Toaster
        position="bottom-center"
        toastOptions={{
          classNames: {
            toast:
              "!glass !rounded-[14px] !text-fg !border-line !text-sm",
            actionButton: "!bg-brand !text-ink !rounded-lg !font-medium",
            cancelButton: "!bg-white/5 !text-fg-muted !rounded-lg",
          },
        }}
      />
    </QueryClientProvider>
  );
}
