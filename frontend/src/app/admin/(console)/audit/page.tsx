"use client";

import { useState } from "react";
import { Panel } from "@/components/ui/panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAudit } from "@/lib/admin/hooks";

// High-risk admin actions get visual emphasis.
const HIGH_RISK = new Set(["admin.user_updated", "admin.login", "user.email_verified"]);

export default function AdminAuditPage() {
  const [page, setPage] = useState(0);
  const limit = 50;
  const { data, isLoading, isError } = useAudit(limit, page * limit);
  const rows = data?.items ?? [];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-medium tracking-tight">Audit log</h1>
        <p className="mt-1 text-sm text-fg-muted">Immutable record of security-relevant events.</p>
      </div>

      <Panel className="overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line text-left text-xs text-fg-subtle">
                <th className="px-4 py-3 font-medium">When</th>
                <th className="px-4 py-3 font-medium">Action</th>
                <th className="px-4 py-3 font-medium">Resource</th>
                <th className="px-4 py-3 font-medium">IP</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && <tr><td colSpan={4} className="px-4 py-8 text-center text-fg-subtle">Loading…</td></tr>}
              {isError && <tr><td colSpan={4} className="px-4 py-8 text-center text-fg-subtle">Couldn&apos;t load the audit log.</td></tr>}
              {data && rows.length === 0 && <tr><td colSpan={4} className="px-4 py-8 text-center text-fg-subtle">No events.</td></tr>}
              {rows.map((r) => (
                <tr key={r.log_id} className="border-b border-line/60">
                  <td className="px-4 py-3 text-fg-muted whitespace-nowrap">
                    {new Date(r.ts).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}
                  </td>
                  <td className="px-4 py-3">
                    {HIGH_RISK.has(r.action)
                      ? <Badge tone="warning">{r.action}</Badge>
                      : <span className="font-mono text-xs text-fg">{r.action}</span>}
                  </td>
                  <td className="px-4 py-3 text-fg-muted">
                    {r.resource ?? "—"}
                    {r.resource_id && <span className="ml-1 font-mono text-[11px] text-fg-subtle">{r.resource_id.slice(0, 8)}</span>}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-fg-subtle">{r.ip_address ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <div className="flex items-center justify-between">
        <Button variant="ghost" size="sm" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>Previous</Button>
        <span className="text-xs text-fg-subtle">Page {page + 1}</span>
        <Button variant="ghost" size="sm" disabled={rows.length < limit} onClick={() => setPage((p) => p + 1)}>Next</Button>
      </div>
    </div>
  );
}
