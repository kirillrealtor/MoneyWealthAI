"use client";

import { useEffect, useState } from "react";
import { usePlaidLink } from "react-plaid-link";
import { toast } from "sonner";
import { Landmark } from "lucide-react";
import { Button, type ButtonProps } from "@/components/ui/button";
import { useCreateLinkToken, useExchangeToken } from "@/lib/api/plaid";

/** Opens Plaid Link with a fetched token, exchanges the public_token on success. */
function Launcher({ token, onClose }: { token: string; onClose: () => void }) {
  const exchange = useExchangeToken();
  const { open, ready } = usePlaidLink({
    token,
    onSuccess: (publicToken) => {
      exchange.mutate(publicToken, {
        onSuccess: (r) => toast.success(`Linked ${r.institution_name ?? "your bank"} — syncing now`),
        onError: () => toast.error("Couldn't finish linking. Please try again."),
        onSettled: onClose,
      });
    },
    onExit: () => onClose(),
  });

  // open() is a side effect (not setState) — safe to call from an effect.
  useEffect(() => {
    if (ready) open();
  }, [ready, open]);

  return null;
}

export function ConnectBankButton({
  children = "Connect a bank",
  ...buttonProps
}: ButtonProps) {
  const create = useCreateLinkToken();
  const [token, setToken] = useState<string | null>(null);

  function start() {
    create.mutate(undefined, {
      onSuccess: (r) => setToken(r.link_token),
      onError: () => toast.error("Couldn't start bank linking. Please retry."),
    });
  }

  return (
    <>
      <Button onClick={start} loading={create.isPending} {...buttonProps}>
        <Landmark className="size-4" />
        {children}
      </Button>
      {token && <Launcher token={token} onClose={() => setToken(null)} />}
    </>
  );
}
