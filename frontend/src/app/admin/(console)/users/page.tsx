"use client";

import { useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAdminUsers } from "@/lib/admin/hooks";

export default function AdminUsersPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const limit = 25;
  const { data, isLoading, isError } = useAdminUsers(search, limit, page * limit);
  const rows = data?.items ?? [];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-medium tracking-tight">Users</h1>
        <p className="mt-1 text-sm text-fg-muted">Search and manage accounts across all tenants.</p>
      </div>

      <div className="relative max-w-sm">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-fg-subtle" />
        <Input
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(0); }}
          placeholder="Search by email or name…"
          className="pl-9"
        />
      </div>

      <Panel className="overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line text-left text-xs text-fg-subtle">
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">Tier</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Joined</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-fg-subtle">Loading…</td></tr>
              )}
              {isError && (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-fg-subtle">Couldn&apos;t load users.</td></tr>
              )}
              {data && rows.length === 0 && (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-fg-subtle">No users match.</td></tr>
              )}
              {rows.map((u) => (
                <tr key={u.user_id} className="border-b border-line/60 transition-colors hover:bg-white/[0.02]">
                  <td className="px-4 py-3">
                    <Link href={`/admin/users/${u.user_id}`} className="font-medium text-fg hover:text-iris">
                      {u.email}
                    </Link>
                    {u.full_name && <span className="ml-2 text-xs text-fg-subtle">{u.full_name}</span>}
                  </td>
                  <td className="px-4 py-3"><Badge tone={u.tier === "free" ? "neutral" : "brand"}>{u.tier}</Badge></td>
                  <td className="px-4 py-3">
                    {u.suspended ? <Badge tone="negative">suspended</Badge>
                      : u.is_verified ? <Badge tone="positive">verified</Badge>
                      : <Badge tone="warning">unverified</Badge>}
                  </td>
                  <td className="px-4 py-3 text-fg-muted">{new Date(u.created_at).toLocaleDateString()}</td>
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
