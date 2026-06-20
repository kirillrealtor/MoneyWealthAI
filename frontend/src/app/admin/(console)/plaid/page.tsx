"use client";

import { toast } from "sonner";
import { Landmark, RefreshCw } from "lucide-react";
import { Panel, PanelHeader } from "@/components/ui/panel";
import { Badge } from "@/components/ui/badge";
import { usePlaidOps, useResync } from "@/lib/admin/hooks";

const STATUS_TONE: Record<string, "positive" | "warning" | "negative" | "neutral"> = {
  completed: "positive",
  running: "neutral",
  pending: "neutral",
  failed: "negative",
};

export default function AdminPlaidOps() {
  const { data, isLoading, isError } = usePlaidOps();
  const resync = useResync();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-medium tracking-tight">Plaid operations</h1>
        <p className="mt-1 text-sm text-fg-muted">Bank connection + sync health. Refreshes every 30s.</p>
      </div>

      {isError && <Panel className="text-sm text-fg-muted">Couldn&apos;t load Plaid metrics.</Panel>}
      {isLoading && <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{Array.from({ length: 4 }).map((_, i) => <div key={i} className="skeleton h-24" />)}</div>}

      {data && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat icon={Landmark} label="Linked items" value={data.health.total_items} />
            <Stat label="Healthy" value={data.health.good_items} tone="positive" />
            <Stat label="Needs attention" value={data.health.error_items} tone={data.health.error_items ? "warn" : undefined} />
            <Stat label="Failed jobs · 24h" value={data.health.failed_jobs_24h} tone={data.health.failed_jobs_24h ? "warn" : undefined} />
          </div>

          <Panel className="overflow-hidden p-0">
            <div className="border-b border-line px-5 py-3"><PanelHeader title="Recent sync jobs" hint={`${data.health.active_jobs} active now`} /></div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-line text-left text-xs text-fg-subtle">
                    <th className="px-4 py-3 font-medium">When</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium">Txns</th>
                    <th className="px-4 py-3 font-medium">Detail</th>
                    <th className="px-4 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {data.jobs.length === 0 && <tr><td colSpan={5} className="px-4 py-8 text-center text-fg-subtle">No sync jobs.</td></tr>}
                  {data.jobs.map((j) => (
                    <tr key={j.sync_id} className="border-b border-line/60">
                      <td className="px-4 py-3 text-fg-muted whitespace-nowrap">{new Date(j.started_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}</td>
                      <td className="px-4 py-3"><Badge tone={STATUS_TONE[j.status] ?? "neutral"}>{j.status}</Badge></td>
                      <td className="px-4 py-3 tabular-nums">{j.transactions_synced}</td>
                      <td className="px-4 py-3 max-w-[280px] truncate text-xs text-fg-subtle" title={j.error_message ?? ""}>{j.error_message ?? "—"}</td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => resync.mutate(j.item_id, { onSuccess: () => toast.success("Re-sync queued"), onError: () => toast.error("Couldn't queue re-sync") })}
                          className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs text-fg-muted hover:bg-hover hover:text-fg"
                        >
                          <RefreshCw className="size-3.5" /> Re-sync
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}

function Stat({ icon: Icon, label, value, tone }: { icon?: typeof Landmark; label: string; value: number; tone?: "positive" | "warn" }) {
  return (
    <Panel>
      <div className="flex items-center justify-between">
        <span className="text-xs text-fg-subtle">{label}</span>
        {Icon && <Icon className="size-4 text-fg-subtle" />}
      </div>
      <p className={`mt-2 text-2xl font-medium tracking-tight tabular-nums ${tone === "positive" ? "text-positive" : tone === "warn" ? "text-warning" : ""}`}>{value.toLocaleString()}</p>
    </Panel>
  );
}
