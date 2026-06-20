"use client";

import { PieChart, Landmark, ArrowRight, TrendingUp, TrendingDown } from "lucide-react";
import { Panel, PanelHeader } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Money } from "@/components/ui/money";
import { usePortfolio } from "@/lib/api/portfolio";

const COLORS = ["#7c3aed", "#8b5cf6", "#6366f1", "#f59e0b", "#f97316", "#a78bfa"];

export default function PortfolioPage() {
  const { data, isLoading, isError } = usePortfolio();
  const hasHoldings = data && data.top_holdings.length > 0;
  const alloc = data ? Object.entries(data.allocation_pct) : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-medium tracking-tight">Portfolio</h1>
        <p className="mt-1 text-sm text-fg-muted">Allocation and concentration — informational, not advice.</p>
      </div>

      {isLoading && <div className="grid gap-4 sm:grid-cols-3">{[0, 1, 2].map((i) => <div key={i} className="skeleton h-28 w-full" />)}</div>}
      {isError && <Panel className="text-sm text-fg-muted">Couldn&apos;t load your portfolio.</Panel>}

      {data && !hasHoldings && (
        <Panel className="flex flex-col items-center py-16 text-center">
          <span className="grid size-12 place-items-center rounded-2xl bg-sky/10 ring-1 ring-sky/20">
            <PieChart className="size-6 text-sky" />
          </span>
          <h3 className="mt-4 text-lg font-medium">No holdings linked</h3>
          <p className="mt-1 max-w-sm text-sm text-fg-muted">
            Connect a brokerage or investment account and MoneyWealth AI will show your allocation, drift
            and concentration at a glance.
          </p>
          <Button className="mt-5">
            <Landmark className="size-4" /> Connect an account <ArrowRight className="size-4" />
          </Button>
        </Panel>
      )}

      {hasHoldings && (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <Panel>
              <p className="text-xs text-fg-subtle">Total value</p>
              <p className="mt-1 text-2xl font-medium tracking-tight"><Money value={data.total_value} /></p>
            </Panel>
            <Panel>
              <p className="text-xs text-fg-subtle">Unrealized P/L</p>
              <p className="mt-1 inline-flex items-center gap-1 text-2xl font-medium tracking-tight">
                {Number(data.unrealized_gain_loss) >= 0 ? <TrendingUp className="size-5 text-positive" /> : <TrendingDown className="size-5 text-negative" />}
                <Money value={data.unrealized_gain_loss} colorize signed />
              </p>
            </Panel>
            <Panel>
              <p className="text-xs text-fg-subtle">Concentration</p>
              <p className="mt-1 text-2xl font-medium tracking-tight">{data.concentration_flags.length || "0"}</p>
              <p className="text-xs text-fg-subtle">flags</p>
            </Panel>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Panel>
              <PanelHeader title="Allocation" />
              <div className="space-y-2.5">
                {alloc.map(([cls, pct], i) => (
                  <div key={cls}>
                    <div className="flex items-center justify-between text-sm">
                      <span className="capitalize text-fg-muted">{cls.replace(/_/g, " ")}</span>
                      <span className="tabular-nums">{Math.round(pct)}%</span>
                    </div>
                    <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-hover">
                      <div className="h-full rounded-full" style={{ width: `${pct}%`, background: COLORS[i % COLORS.length] }} />
                    </div>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel>
              <PanelHeader title="Top holdings" />
              <div className="divide-y divide-line">
                {data.top_holdings.map((h, i) => (
                  <div key={i} className="flex items-center justify-between py-2.5 text-sm">
                    <span className="truncate text-fg">{h.name ?? "—"}</span>
                    <span className="tabular-nums">{h.value ? <Money value={h.value} /> : "—"}</span>
                  </div>
                ))}
              </div>
            </Panel>
          </div>

          {data.concentration_flags.length > 0 && (
            <Panel>
              <PanelHeader title="Concentration flags" />
              <div className="flex flex-wrap gap-2">
                {data.concentration_flags.map((f) => <Badge key={f} tone="warning">{f}</Badge>)}
              </div>
            </Panel>
          )}
        </>
      )}
    </div>
  );
}
