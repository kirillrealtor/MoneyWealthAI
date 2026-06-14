"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { toast } from "sonner";
import { ArrowLeft, Ban, CheckCircle2, ShieldCheck } from "lucide-react";
import { Panel, PanelHeader } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Field } from "@/components/ui/input";
import { useAdminUser, useUpdateUser } from "@/lib/admin/hooks";

export default function AdminUserDetailPage() {
  const id = String(useParams().id);
  const { data: u, isLoading, isError } = useAdminUser(id);
  const update = useUpdateUser(id);
  const [tier, setTier] = useState<string | null>(null);

  function patch(body: { tier?: string; suspended?: boolean; is_verified?: boolean; reason?: string }, label: string) {
    update.mutate(body, {
      onSuccess: () => toast.success(label),
      onError: () => toast.error("Action failed."),
    });
  }

  return (
    <div className="space-y-6">
      <Link href="/admin/users" className="inline-flex items-center gap-1.5 text-sm text-fg-muted hover:text-fg">
        <ArrowLeft className="size-4" /> Users
      </Link>

      {isLoading && <div className="skeleton h-40" />}
      {isError && <Panel className="text-sm text-fg-muted">Couldn&apos;t load this user.</Panel>}

      {u && (
        <>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-medium tracking-tight">{u.email}</h1>
              <p className="mt-1 text-sm text-fg-subtle">{u.full_name || "No name set"} · joined {new Date(u.created_at).toLocaleDateString()}</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge tone={u.tier === "free" ? "neutral" : "brand"}>{u.tier}</Badge>
              {u.suspended ? <Badge tone="negative">suspended</Badge> : u.is_verified ? <Badge tone="positive">verified</Badge> : <Badge tone="warning">unverified</Badge>}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <Panel><p className="text-xs text-fg-subtle">Budgets</p><p className="mt-1 text-2xl font-medium tabular-nums">{u.budget_count}</p></Panel>
            <Panel><p className="text-xs text-fg-subtle">Goals</p><p className="mt-1 text-2xl font-medium tabular-nums">{u.goal_count}</p></Panel>
            <Panel><p className="text-xs text-fg-subtle">Linked banks</p><p className="mt-1 text-2xl font-medium tabular-nums">{u.linked_items}</p></Panel>
          </div>

          <Panel>
            <PanelHeader title="Actions" hint="Every change is recorded in the audit log" />
            <div className="space-y-5">
              <div className="flex flex-wrap items-end gap-3">
                <Field label="Tier" htmlFor="tier">
                  <Select id="tier" value={tier ?? u.tier} onChange={(e) => setTier(e.target.value)} className="w-40">
                    <option value="free">free</option>
                    <option value="plus">plus</option>
                    <option value="premium">premium</option>
                  </Select>
                </Field>
                <Button
                  variant="secondary"
                  disabled={update.isPending || (tier ?? u.tier) === u.tier}
                  onClick={() => patch({ tier: tier ?? u.tier, reason: "admin tier change" }, "Tier updated")}
                >
                  Save tier
                </Button>
              </div>

              <div className="flex flex-wrap gap-3 border-t border-line pt-5">
                {!u.is_verified && (
                  <Button variant="secondary" onClick={() => patch({ is_verified: true, reason: "manual verify" }, "User verified")}>
                    <CheckCircle2 className="size-4" /> Mark verified
                  </Button>
                )}
                {u.suspended ? (
                  <Button variant="secondary" onClick={() => patch({ suspended: false, reason: "unsuspend" }, "User reinstated")}>
                    <ShieldCheck className="size-4" /> Reinstate
                  </Button>
                ) : (
                  <Button variant="danger" onClick={() => patch({ suspended: true, reason: "admin suspend" }, "User suspended")}>
                    <Ban className="size-4" /> Suspend
                  </Button>
                )}
              </div>
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}
