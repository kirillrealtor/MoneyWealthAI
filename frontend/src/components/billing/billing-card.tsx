"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Check, Sparkles, ExternalLink } from "lucide-react";
import { Panel, PanelHeader } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth/context";
import { useSubscription, useStartCheckout, useOpenPortal } from "@/lib/api/billing";

const PLANS = [
  { id: "plus" as const, name: "Plus", monthly: 12, annual: 120, features: ["Debt & portfolio tools", "Deeper advisor + scenarios", "Proactive alerts"] },
  { id: "premium" as const, name: "Premium", monthly: 29, annual: 290, features: ["Everything in Plus", "Unlimited advisor depth", "Household accounts"] },
];

export function BillingCard() {
  const { user } = useAuth();
  const { data: sub } = useSubscription();
  const checkout = useStartCheckout();
  const portal = useOpenPortal();
  const [annual, setAnnual] = useState(true);
  const tier = user?.tier ?? "free";
  const paid = tier !== "free";

  // Reflect Stripe Checkout's redirect back (?billing=success|cancelled).
  useEffect(() => {
    const p = new URLSearchParams(window.location.search).get("billing");
    if (p === "success") toast.success("You're upgraded — welcome aboard!");
    else if (p === "cancelled") toast("Checkout cancelled — no changes made.");
    if (p) window.history.replaceState({}, "", window.location.pathname);
  }, []);

  return (
    <Panel>
      <PanelHeader
        title="Plan & billing"
        hint="Manage your subscription"
        action={<Badge tone={paid ? "brand" : "neutral"}>{tier} plan</Badge>}
      />

      {paid ? (
        <div className="space-y-4">
          <p className="text-sm text-fg-muted">
            You&apos;re on <span className="font-medium text-fg capitalize">{tier}</span>
            {sub?.cancel_at_period_end && sub.current_period_end
              ? ` — cancels ${new Date(sub.current_period_end).toLocaleDateString()}`
              : sub?.current_period_end
                ? ` — renews ${new Date(sub.current_period_end).toLocaleDateString()}`
                : ""}
            .
          </p>
          <Button variant="secondary" onClick={() => portal.mutate()} loading={portal.isPending}>
            <ExternalLink className="size-4" /> Manage billing
          </Button>
        </div>
      ) : (
        <div className="space-y-5">
          <div className="flex items-center gap-3">
            <span className={annual ? "text-sm text-fg-subtle" : "text-sm text-fg"}>Monthly</span>
            <button
              role="switch"
              aria-checked={annual}
              aria-label="Toggle annual billing"
              onClick={() => setAnnual((a) => !a)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${annual ? "bg-brand" : "bg-black/10"}`}
            >
              <span className={`inline-block size-5 rounded-full bg-white transition-transform ${annual ? "translate-x-[22px]" : "translate-x-0.5"}`} />
            </button>
            <span className={annual ? "text-sm text-fg" : "text-sm text-fg-subtle"}>Annual <span className="text-brand">save ~17%</span></span>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {PLANS.map((p) => {
              const price = annual ? Math.round(p.annual / 12) : p.monthly;
              const pending = checkout.isPending && checkout.variables?.plan === p.id;
              return (
                <div key={p.id} className="rounded-[14px] border border-line p-4">
                  <div className="flex items-center gap-1.5">
                    {p.id === "premium" && <Sparkles className="size-4 text-brand" />}
                    <p className="font-medium">{p.name}</p>
                  </div>
                  <p className="mt-1"><span className="text-2xl font-medium tabular-nums">${price}</span><span className="text-sm text-fg-subtle">/mo</span></p>
                  <ul className="mt-3 space-y-1.5">
                    {p.features.map((f) => (
                      <li key={f} className="flex items-start gap-1.5 text-xs text-fg-muted"><Check className="mt-0.5 size-3.5 shrink-0 text-brand" /> {f}</li>
                    ))}
                  </ul>
                  <Button
                    className="mt-4 w-full"
                    variant={p.id === "plus" ? "primary" : "secondary"}
                    loading={pending}
                    onClick={() => checkout.mutate({ plan: p.id, interval: annual ? "annual" : "monthly" }, {
                      onError: () => toast.error("Couldn't start checkout. Billing may not be enabled yet."),
                    })}
                  >
                    Upgrade to {p.name}
                  </Button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </Panel>
  );
}
