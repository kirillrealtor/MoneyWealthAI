"use client";

import { useEffect, useState } from "react";
import { usePlaidLink } from "react-plaid-link";
import { toast } from "sonner";
import { Landmark, ShieldCheck, Beaker } from "lucide-react";
import { Button, type ButtonProps } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { useCreateLinkToken, useExchangeToken } from "@/lib/api/plaid";

/** Opens Plaid Link with a fetched token, exchanges the public_token on success. */
function Launcher({ token, environment, onClose }: { token: string; environment: string; onClose: () => void }) {
  const exchange = useExchangeToken();
  const { open, ready } = usePlaidLink({
    token,
    onSuccess: (publicToken) => {
      exchange.mutate(
        { public_token: publicToken, environment },
        {
          onSuccess: (r) => toast.success(`Linked ${r.institution_name ?? "your bank"} — syncing now`),
          onError: () => toast.error("Couldn't finish linking. Please try again."),
          onSettled: onClose,
        }
      );
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
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedEnv, setSelectedEnv] = useState<string | null>(null);

  function handleSelect(env: string) {
    setSelectedEnv(env);
    create.mutate(env, {
      onSuccess: (r) => {
        setToken(r.link_token);
        setOpenDialog(false);
      },
      onError: () => {
        toast.error("Couldn't start bank linking. Please retry.");
        setSelectedEnv(null);
      },
    });
  }

  function handleCloseDialog(open: boolean) {
    if (!create.isPending) {
      setOpenDialog(open);
    }
  }

  return (
    <>
      <Button onClick={() => setOpenDialog(true)} {...buttonProps}>
        <Landmark className="size-4" />
        {children}
      </Button>

      <Dialog open={openDialog} onOpenChange={handleCloseDialog}>
        <DialogContent
          title="Connect a bank account"
          description="Choose whether to connect a test sandbox account or link a real bank account."
        >
          <div className="mt-4 space-y-3">
            <button
              disabled={create.isPending}
              onClick={() => handleSelect("sandbox")}
              className="flex w-full items-start gap-4 rounded-xl border border-line p-4 text-left transition-all hover:bg-hover hover:border-brand/40 disabled:opacity-50"
            >
              <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand/10 ring-1 ring-brand/20">
                {create.isPending && selectedEnv === "sandbox" ? (
                  <span className="animate-spin size-4 border-2 border-brand border-t-transparent rounded-full" />
                ) : (
                  <Beaker className="size-5 text-brand" />
                )}
              </span>
              <div>
                <p className="font-medium text-fg">Sandbox Account (Testing)</p>
                <p className="mt-1 text-xs text-fg-muted">
                  Use for testing and development. Search for &quot;Platypus&quot; and login with user_good / pass_good.
                </p>
              </div>
            </button>

            <button
              disabled={create.isPending}
              onClick={() => handleSelect("development")}
              className="flex w-full items-start gap-4 rounded-xl border border-line p-4 text-left transition-all hover:bg-hover hover:border-brand/40 disabled:opacity-50"
            >
              <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-positive/10 ring-1 ring-positive/20">
                {create.isPending && selectedEnv === "development" ? (
                  <span className="animate-spin size-4 border-2 border-positive border-t-transparent rounded-full" />
                ) : (
                  <ShieldCheck className="size-5 text-positive" />
                )}
              </span>
              <div>
                <p className="font-medium text-fg">Real Bank Account (Live)</p>
                <p className="mt-1 text-xs text-fg-muted">
                  Connect your actual, live bank accounts securely through Plaid.
                </p>
              </div>
            </button>
          </div>
        </DialogContent>
      </Dialog>

      {token && selectedEnv && (
        <Launcher token={token} environment={selectedEnv} onClose={() => { setToken(null); setSelectedEnv(null); }} />
      )}
    </>
  );
}
