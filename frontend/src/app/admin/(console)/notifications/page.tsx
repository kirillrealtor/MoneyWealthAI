"use client";

import { useState } from "react";
import { toast } from "sonner";
import { RefreshCw } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useOutbox, useRetryOutbox } from "@/lib/admin/hooks";

const TONE: Record<string, "positive" | "warning" | "negative" | "neutral"> = {
  sent: "positive",
  pending: "neutral",
  failed: "negative",
  skipped: "warning",
};

export default function AdminOutboxPage() {
  const [status, setStatus] = useState("");
  const { data, isLoading, isError } = useOutbox(status);
  const retry = useRetryOutbox();
  const rows = data?.items ?? [];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-medium tracking-tight">Notification outbox</h1>
          <p className="mt-1 text-sm text-fg-muted">Delivery log across channels. Re-queue failures. Refreshes every 30s.</p>
        </div>
        <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-40">
          <option value="">All statuses</option>
          <option value="sent">Sent</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
          <option value="skipped">Skipped</option>
        </Select>
      </div>

      {isError && <Panel className="text-sm text-fg-muted">Couldn&apos;t load the outbox.</Panel>}
      {isLoading && <div className="space-y-2">{[0, 1, 2].map((i) => <div key={i} className="skeleton h-14 w-full" />)}</div>}

      {data && (
        <Panel className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left text-xs text-fg-subtle">
                  <th className="px-4 py-3 font-medium">When</th>
                  <th className="px-4 py-3 font-medium">Channel</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Attempts</th>
                  <th className="px-4 py-3 font-medium">Error</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 && <tr><td colSpan={6} className="px-4 py-8 text-center text-fg-subtle">No deliveries.</td></tr>}
                {rows.map((r) => (
                  <tr key={r.outbox_id} className="border-b border-line/60">
                    <td className="px-4 py-3 text-fg-muted whitespace-nowrap">{new Date(r.created_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}</td>
                    <td className="px-4 py-3 capitalize">{r.channel}</td>
                    <td className="px-4 py-3"><Badge tone={TONE[r.status] ?? "neutral"}>{r.status}</Badge></td>
                    <td className="px-4 py-3 tabular-nums">{r.attempts}</td>
                    <td className="px-4 py-3 max-w-[240px] truncate text-xs text-fg-subtle" title={r.error ?? ""}>{r.error ?? "—"}</td>
                    <td className="px-4 py-3 text-right">
                      {r.status === "failed" && (
                        <button
                          onClick={() => retry.mutate(r.outbox_id, { onSuccess: () => toast.success("Re-queued"), onError: () => toast.error("Couldn't re-queue") })}
                          className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs text-fg-muted hover:bg-hover hover:text-fg"
                        >
                          <RefreshCw className="size-3.5" /> Retry
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  );
}
