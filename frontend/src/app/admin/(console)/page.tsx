"use client";

import { Users, UserCheck, UserX, TrendingUp, Wallet, Target, Landmark } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { useKpis } from "@/lib/admin/hooks";

export default function AdminOverview() {
  const { data, isLoading, isError } = useKpis();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-medium tracking-tight">Overview</h1>
        <p className="mt-1 text-sm text-fg-muted">Platform health at a glance.</p>
      </div>

      {isError && <Panel className="text-sm text-fg-muted">Couldn&apos;t load metrics.</Panel>}
      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{Array.from({ length: 8 }).map((_, i) => <div key={i} className="skeleton h-24" />)}</div>
      )}

      {data && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat icon={Users} label="Total users" value={data.total_users} />
            <Stat icon={UserCheck} label="Verified" value={data.verified_users} />
            <Stat icon={UserX} label="Suspended" value={data.suspended_users} tone={data.suspended_users ? "warn" : undefined} />
            <Stat icon={TrendingUp} label="Signups today" value={data.signups_today} accent />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat icon={TrendingUp} label="Signups · 7d" value={data.signups_7d} />
            <Stat icon={TrendingUp} label="Signups · 30d" value={data.signups_30d} />
            <Stat icon={Landmark} label="Linked banks" value={data.linked_items} />
            <Stat icon={Wallet} label="Budgets" value={data.total_budgets} />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat icon={Target} label="Goals" value={data.total_goals} />
          </div>
          <p className="text-xs text-fg-subtle">
            Aggregates read via audited cross-tenant functions. At scale these come from pre-aggregated rollups.
          </p>
        </>
      )}
    </div>
  );
}

function Stat({
  icon: Icon,
  label,
  value,
  accent,
  tone,
}: {
  icon: typeof Users;
  label: string;
  value: number;
  accent?: boolean;
  tone?: "warn";
}) {
  return (
    <Panel>
      <div className="flex items-center justify-between">
        <span className="text-xs text-fg-subtle">{label}</span>
        <Icon className={tone === "warn" ? "size-4 text-warning" : accent ? "size-4 text-iris" : "size-4 text-fg-subtle"} />
      </div>
      <p className="mt-2 text-3xl font-medium tracking-tight tabular-nums">{value.toLocaleString()}</p>
    </Panel>
  );
}
