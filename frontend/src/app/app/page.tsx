"use client";

import Link from "next/link";
import { ArrowRight, Sparkles, Landmark, Plus, Wallet, Target } from "lucide-react";
import { useAuth } from "@/lib/auth/context";
import { Panel, PanelHeader } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Money } from "@/components/ui/money";
import { useBudgets } from "@/lib/api/budgets";
import { useGoals } from "@/lib/api/goals";

export default function DashboardPage() {
  const { user } = useAuth();
  const name = user?.full_name?.split(" ")[0] || "there";
  const { data: budgets } = useBudgets();
  const { data: goals } = useGoals();

  const totalLimit = budgets?.reduce((s, b) => s + Number(b.monthly_limit), 0) ?? 0;
  const totalSpent = budgets?.reduce((s, b) => s + Number(b.spent), 0) ?? 0;
  const goalProgress =
    goals && goals.length
      ? Math.round(
          (goals.reduce((s, g) => s + Number(g.current_amount), 0) /
            Math.max(goals.reduce((s, g) => s + Number(g.target_amount), 0), 1)) *
            100,
        )
      : 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm text-fg-subtle">{greeting()},</p>
          <h1 className="text-3xl font-medium tracking-tight">
            {name}
            <span className="font-display italic text-aurora">.</span>
          </h1>
        </div>
        <Button variant="secondary" size="sm">
          <Plus className="size-4" /> Connect a bank
        </Button>
      </div>

      {/* real summaries */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Link href="/app/budgets">
          <Panel interactive className="h-full">
            <PanelHeader title="Budgets" hint={`${budgets?.length ?? 0} active`} action={<Wallet className="size-5 text-brand" />} />
            {budgets && budgets.length > 0 ? (
              <>
                <p className="text-2xl font-medium tracking-tight">
                  <Money value={String(totalSpent)} /> <span className="text-base text-fg-subtle">/ <Money value={String(totalLimit)} /></span>
                </p>
                <p className="mt-1 text-xs text-fg-subtle">spent across categories this month</p>
              </>
            ) : (
              <p className="text-sm text-fg-muted">Set your first budget →</p>
            )}
          </Panel>
        </Link>

        <Link href="/app/goals">
          <Panel interactive className="h-full">
            <PanelHeader title="Goals" hint={`${goals?.length ?? 0} active`} action={<Target className="size-5 text-iris" />} />
            {goals && goals.length > 0 ? (
              <>
                <p className="text-2xl font-medium tracking-tight tnum">{goalProgress}%</p>
                <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-white/5">
                  <div className="h-full rounded-full bg-gradient-to-r from-brand to-sky" style={{ width: `${goalProgress}%` }} />
                </div>
              </>
            ) : (
              <p className="text-sm text-fg-muted">Create your first goal →</p>
            )}
          </Panel>
        </Link>

        <Panel className="h-full">
          <PanelHeader title="Net worth" hint="Across linked accounts" action={<Landmark className="size-5 text-fg-muted" />} />
          <div className="flex h-[68px] items-center justify-center rounded-[12px] border border-dashed border-line text-sm text-fg-subtle">
            Connect a bank to see this
          </div>
        </Panel>
      </div>

      {/* first-run: connect a bank */}
      <Panel className="relative overflow-hidden p-8 sm:p-10">
        <div className="absolute -right-10 -top-10 size-48 rounded-full bg-brand/15 blur-3xl" />
        <div className="relative max-w-lg">
          <Badge tone="brand">
            <Sparkles className="size-3.5" /> Bring it to life
          </Badge>
          <h2 className="mt-4 text-2xl font-medium tracking-tight">
            Connect a bank to unlock your full picture.
          </h2>
          <p className="mt-2 text-fg-muted">
            Link an account securely through Plaid — read-only, encrypted — and your net worth,
            spending and advisor fill in with real numbers.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button>
              <Landmark className="size-4" /> Connect a bank <ArrowRight className="size-4" />
            </Button>
          </div>
        </div>
      </Panel>
    </div>
  );
}

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}
