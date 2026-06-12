"use client";

import { useState } from "react";
import Link from "next/link";
import { Check } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const PLANS = [
  {
    name: "Free",
    monthly: 0,
    annual: 0,
    note: "For getting started",
    features: ["All dashboards", "Budgets & goals", "100 advisor messages / mo", "Bank-level security"],
    cta: "Start free",
    highlight: false,
  },
  {
    name: "Plus",
    monthly: 12,
    annual: 120,
    note: "For getting ahead",
    features: ["Everything in Free", "Debt & portfolio tools", "Deeper advisor + scenarios", "Proactive alerts", "Unlimited budgets & goals"],
    cta: "Start Plus",
    highlight: true,
  },
  {
    name: "Premium",
    monthly: 29,
    annual: 290,
    note: "For full command",
    features: ["Everything in Plus", "Unlimited advisor depth", "Household accounts", "Priority guidance"],
    cta: "Go Premium",
    highlight: false,
  },
];

export function PricingTable() {
  const [annual, setAnnual] = useState(true);

  return (
    <div>
      {/* toggle */}
      <div className="mb-10 flex items-center justify-center gap-3">
        <span className={annual ? "text-sm text-fg-subtle" : "text-sm text-fg"}>Monthly</span>
        <button
          role="switch"
          aria-checked={annual}
          aria-label="Toggle annual billing"
          onClick={() => setAnnual((a) => !a)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${annual ? "bg-brand" : "bg-white/10"}`}
        >
          <span className={`inline-block size-5 rounded-full bg-white transition-transform ${annual ? "translate-x-[22px]" : "translate-x-0.5"}`} />
        </button>
        <span className={annual ? "text-sm text-fg" : "text-sm text-fg-subtle"}>
          Annual <span className="text-brand">· save ~17%</span>
        </span>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {PLANS.map((p) => {
          const price = annual ? Math.round(p.annual / 12) : p.monthly;
          return (
            <Panel key={p.name} className={p.highlight ? "relative ring-glow border-brand/30" : "relative"}>
              {p.highlight && <Badge tone="brand" className="absolute -top-3 left-6">Most popular</Badge>}
              <p className="text-sm font-medium text-fg-muted">{p.name}</p>
              <p className="mt-0.5 text-xs text-fg-subtle">{p.note}</p>
              <p className="mt-4">
                <span className="text-4xl font-medium tracking-tight tabular-nums">${price}</span>
                <span className="ml-1.5 text-sm text-fg-subtle">/mo</span>
              </p>
              <p className="mt-1 h-4 text-xs text-fg-subtle">
                {annual && p.annual > 0 ? `billed $${p.annual} annually` : ""}
              </p>
              <ul className="mt-5 space-y-2.5">
                {p.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-fg-muted">
                    <Check className="mt-0.5 size-4 shrink-0 text-brand" /> {f}
                  </li>
                ))}
              </ul>
              <Link href="/signup" className="mt-6 block">
                <Button variant={p.highlight ? "primary" : "secondary"} className="w-full">{p.cta}</Button>
              </Link>
            </Panel>
          );
        })}
      </div>
    </div>
  );
}
