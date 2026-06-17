"use client";

import { Sparkles, AlertTriangle, Coins, Activity, ShieldAlert } from "lucide-react";
import { Panel, PanelHeader } from "@/components/ui/panel";
import { Badge } from "@/components/ui/badge";
import { useAiOps } from "@/lib/admin/hooks";

const TIER = ["healthy", "degraded", "critical"] as const;
const TIER_TONE = ["positive", "warning", "negative"] as const;

export default function AdminAiOps() {
  const { data, isLoading, isError } = useAiOps();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-medium tracking-tight">AI operations</h1>
        <p className="mt-1 text-sm text-fg-muted">Advisor health, cost and usage. Refreshes every 30s.</p>
      </div>

      {isError && <Panel className="text-sm text-fg-muted">Couldn&apos;t load AI metrics.</Panel>}
      {isLoading && <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{Array.from({ length: 4 }).map((_, i) => <div key={i} className="skeleton h-24" />)}</div>}

      {data && (
        <>
          <Panel className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Sparkles className="size-5 text-iris" />
              <div>
                <p className="text-sm font-medium">Advisor status</p>
                <p className="text-xs text-fg-subtle">Degradation tier {data.stats.tier}</p>
              </div>
            </div>
            <Badge tone={TIER_TONE[data.stats.tier] ?? "neutral"}>{TIER[data.stats.tier] ?? "unknown"}</Badge>
          </Panel>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat icon={Activity} label="Calls" value={data.stats.calls_total.toLocaleString()} />
            <Stat icon={AlertTriangle} label="Error rate" value={`${(data.stats.error_rate * 100).toFixed(1)}%`} warn={data.stats.error_rate > 0.05} />
            <Stat icon={Coins} label="Tokens" value={data.stats.tokens_total.toLocaleString()} />
            <Stat icon={ShieldAlert} label="Validation fails" value={data.stats.validation_failures.toLocaleString()} warn={data.stats.validation_failures > 0} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Panel>
              <PanelHeader title="Daily token usage" hint="Last 14 days" />
              <UsageBars usage={data.usage} />
            </Panel>

            <Panel>
              <PanelHeader title="Top spenders today" />
              {data.top_users.length === 0 ? (
                <p className="py-6 text-center text-sm text-fg-subtle">No usage today.</p>
              ) : (
                <div className="divide-y divide-line">
                  {data.top_users.map((u) => (
                    <div key={u.user_id} className="flex items-center justify-between py-2 text-sm">
                      <span className="truncate text-fg-muted">{u.email}</span>
                      <span className="tabular-nums">{u.tokens.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              )}
            </Panel>
          </div>

          <Panel>
            <PanelHeader title="Per-tier daily token budget" hint="Cost guardrail enforced before each turn" />
            <div className="flex flex-wrap gap-6 text-sm">
              <span>Free <span className="ml-1 font-medium tabular-nums">{data.tier_budgets.free.toLocaleString()}</span></span>
              <span>Plus <span className="ml-1 font-medium tabular-nums">{data.tier_budgets.plus.toLocaleString()}</span></span>
              <span>Premium <span className="ml-1 font-medium tabular-nums">{data.tier_budgets.premium.toLocaleString()}</span></span>
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}

function Stat({ icon: Icon, label, value, warn }: { icon: typeof Activity; label: string; value: string; warn?: boolean }) {
  return (
    <Panel>
      <div className="flex items-center justify-between">
        <span className="text-xs text-fg-subtle">{label}</span>
        <Icon className={warn ? "size-4 text-warning" : "size-4 text-fg-subtle"} />
      </div>
      <p className="mt-2 text-2xl font-medium tracking-tight tabular-nums">{value}</p>
    </Panel>
  );
}

function UsageBars({ usage }: { usage: { day: string; tokens: number }[] }) {
  const max = Math.max(1, ...usage.map((u) => u.tokens));
  return (
    <div className="flex h-32 items-end gap-1.5">
      {usage.map((u) => (
        <div key={u.day} className="flex flex-1 flex-col items-center gap-1" title={`${u.day}: ${u.tokens.toLocaleString()}`}>
          <div className="w-full rounded-t bg-gradient-to-t from-iris/40 to-iris" style={{ height: `${Math.max(2, (u.tokens / max) * 100)}%` }} />
          <span className="text-[9px] text-fg-subtle">{u.day.slice(5)}</span>
        </div>
      ))}
      {usage.length === 0 && <p className="w-full py-6 text-center text-sm text-fg-subtle">No data.</p>}
    </div>
  );
}
