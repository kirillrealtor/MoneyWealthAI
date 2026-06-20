"use client";

import Link from "next/link";
import { ArrowRight, Sparkles, Landmark, Wallet, Target, MessageSquare } from "lucide-react";
import { useAuth } from "@/lib/auth/context";
import { Panel, PanelHeader } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Money } from "@/components/ui/money";
import { useBudgets } from "@/lib/api/budgets";
import { useGoals } from "@/lib/api/goals";
import { usePlaidItems, type PlaidItem } from "@/lib/api/plaid";

export default function DashboardPage() {
  const { user } = useAuth();
  const name = user?.full_name?.split(" ")[0] || "there";
  const { data: budgets, isLoading: budgetsLoading } = useBudgets();
  const { data: goals, isLoading: goalsLoading } = useGoals();
  const { data: items, isLoading: itemsLoading } = usePlaidItems();

  const nw = items ? netWorth(items) : null;
  const linked = (nw?.accounts ?? 0) > 0;

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
      {/* header — one clear, context-aware action */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm text-fg-subtle">{greeting()},</p>
          <h1 className="text-3xl font-medium tracking-tight">
            {name}
            <span className="font-display italic text-aurora">.</span>
          </h1>
        </div>
        <Link href="/app/advisor">
          <Button variant="secondary" size="sm">
            <Sparkles className="size-4" /> Ask your advisor
          </Button>
        </Link>
      </div>

      {/* summaries */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {/* Net worth — real figure once linked */}
        <Link href="/app/accounts" aria-label="View linked accounts">
          <Panel interactive className="h-full">
            <PanelHeader
              title="Net worth"
              hint={linked ? `${nw!.accounts} account${nw!.accounts === 1 ? "" : "s"}` : "Across linked accounts"}
              action={<Landmark className="size-5 text-fg-muted" />}
            />
            {itemsLoading ? (
              <Skeleton className="h-8 w-32" />
            ) : linked ? (
              <>
                <p className="text-2xl font-medium tracking-tight">
                  <Money value={String(nw!.value)} colorize />
                </p>
                <p className="mt-1 text-xs text-fg-subtle">assets minus debt, live</p>
              </>
            ) : (
              <div className="flex h-[68px] items-center justify-center rounded-[12px] border border-dashed border-line text-sm text-fg-subtle">
                Connect a bank to see this
              </div>
            )}
          </Panel>
        </Link>

        {/* Budgets */}
        <Link href="/app/budgets">
          <Panel interactive className="h-full">
            <PanelHeader title="Budgets" hint={`${budgets?.length ?? 0} active`} action={<Wallet className="size-5 text-brand" />} />
            {budgetsLoading ? (
              <Skeleton className="h-8 w-40" />
            ) : budgets && budgets.length > 0 ? (
              <>
                <p className="text-2xl font-medium tracking-tight">
                  <Money value={String(totalSpent)} />{" "}
                  <span className="text-base text-fg-subtle">
                    / <Money value={String(totalLimit)} />
                  </span>
                </p>
                <p className="mt-1 text-xs text-fg-subtle">spent across categories this month</p>
              </>
            ) : (
              <p className="inline-flex items-center gap-1 text-sm text-brand">
                Set your first budget <ArrowRight className="size-3.5" />
              </p>
            )}
          </Panel>
        </Link>

        {/* Goals */}
        <Link href="/app/goals">
          <Panel interactive className="h-full">
            <PanelHeader title="Goals" hint={`${goals?.length ?? 0} active`} action={<Target className="size-5 text-iris" />} />
            {goalsLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : goals && goals.length > 0 ? (
              <>
                <p className="text-2xl font-medium tracking-tight tnum">{goalProgress}%</p>
                <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-black/5">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-brand to-sky transition-[width] duration-500"
                    style={{ width: `${goalProgress}%` }}
                  />
                </div>
              </>
            ) : (
              <p className="inline-flex items-center gap-1 text-sm text-iris">
                Create your first goal <ArrowRight className="size-3.5" />
              </p>
            )}
          </Panel>
        </Link>
      </div>

      {/* contextual hero: onboard new users, otherwise point to the advisor */}
      {!itemsLoading && (linked ? <AdvisorHero name={name} /> : <ConnectHero />)}
    </div>
  );
}

function Skeleton({ className }: { className?: string }) {
  return <div className={`skeleton ${className ?? ""}`} />;
}

function ConnectHero() {
  return (
    <Panel className="relative overflow-hidden p-8 sm:p-10">
      <div className="absolute -right-10 -top-10 size-48 rounded-full bg-brand/15 blur-3xl" />
      <div className="relative max-w-lg">
        <Badge tone="brand">
          <Sparkles className="size-3.5" /> Bring it to life
        </Badge>
        <h2 className="mt-4 text-2xl font-medium tracking-tight">Connect a bank to unlock your full picture.</h2>
        <p className="mt-2 text-fg-muted">
          Link an account securely through Plaid — read-only, encrypted — and your net worth, spending and
          advisor fill in with real numbers.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/app/accounts">
            <Button>
              <Landmark className="size-4" /> Connect a bank <ArrowRight className="size-4" />
            </Button>
          </Link>
        </div>
      </div>
    </Panel>
  );
}

function AdvisorHero({ name }: { name: string }) {
  return (
    <Panel className="relative overflow-hidden p-8 sm:p-10">
      <div className="absolute -right-10 -top-10 size-48 rounded-full bg-iris/15 blur-3xl" />
      <div className="relative max-w-lg">
        <Badge tone="brand">
          <Sparkles className="size-3.5" /> Grounded in your data
        </Badge>
        <h2 className="mt-4 text-2xl font-medium tracking-tight">
          Ask {name === "there" ? "" : `${name}, `}what should you do next?
        </h2>
        <p className="mt-2 text-fg-muted">
          Your advisor reads your real budgets, goals, spending and debt to answer — with numbers it can
          trace, never invent.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/app/advisor">
            <Button>
              <MessageSquare className="size-4" /> Talk to your advisor <ArrowRight className="size-4" />
            </Button>
          </Link>
        </div>
      </div>
    </Panel>
  );
}

/** Net worth = assets − liabilities, classified by Plaid account type. */
function netWorth(items: PlaidItem[]): { value: number; accounts: number } {
  let assets = 0;
  let liabilities = 0;
  let accounts = 0;
  for (const item of items) {
    for (const a of item.accounts) {
      if (a.balance_current == null) continue;
      accounts++;
      const bal = Number(a.balance_current);
      if (a.type === "credit" || a.type === "loan") liabilities += bal;
      else assets += bal;
    }
  }
  return { value: assets - liabilities, accounts };
}

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}
