"use client";

import { useState } from "react";
import { Search, Receipt } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Money } from "@/components/ui/money";
import { useTransactions } from "@/lib/api/transactions";
import { PLAID_CATEGORIES, categoryLabel } from "@/lib/api/types";

export default function TransactionsPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [page, setPage] = useState(0);
  const limit = 50;
  const { data, isLoading, isError } = useTransactions({ search, category, limit, offset: page * limit });
  const rows = data?.items ?? [];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-medium tracking-tight">Transactions</h1>
        <p className="mt-1 text-sm text-fg-muted">Everything across your linked accounts.</p>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-fg-subtle" />
          <Input value={search} onChange={(e) => { setSearch(e.target.value); setPage(0); }} placeholder="Search merchant…" className="pl-9" />
        </div>
        <Select value={category} onChange={(e) => { setCategory(e.target.value); setPage(0); }} className="w-52">
          <option value="">All categories</option>
          {PLAID_CATEGORIES.map((c) => <option key={c} value={c}>{categoryLabel(c)}</option>)}
        </Select>
      </div>

      {isLoading && <div className="space-y-2">{Array.from({ length: 8 }).map((_, i) => <div key={i} className="skeleton h-14 w-full" />)}</div>}
      {isError && <Panel className="text-sm text-fg-muted">Couldn&apos;t load transactions.</Panel>}

      {data && rows.length === 0 && (
        <Panel className="flex flex-col items-center py-14 text-center">
          <span className="grid size-12 place-items-center rounded-2xl bg-hover ring-1 ring-line"><Receipt className="size-6 text-fg-muted" /></span>
          <h3 className="mt-4 text-lg font-medium">No transactions</h3>
          <p className="mt-1 max-w-xs text-sm text-fg-muted">{search || category ? "Try a different filter." : "Connect a bank to see your transactions here."}</p>
        </Panel>
      )}

      {rows.length > 0 && (
        <Panel className="overflow-hidden p-0">
          <div className="divide-y divide-line">
            {rows.map((t) => (
              <div key={t.transaction_id} className="flex items-center justify-between gap-4 px-4 py-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-fg">{t.merchant_name ?? "Transaction"}</p>
                  <p className="mt-0.5 flex items-center gap-2 text-xs text-fg-subtle">
                    <span>{new Date(t.date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}</span>
                    {t.category && <span className="capitalize">· {categoryLabel(t.category)}</span>}
                    {t.pending && <Badge tone="neutral">pending</Badge>}
                  </p>
                </div>
                {/* Plaid: positive amount = money out. Show spend as negative (coral). */}
                <Money value={-Number(t.amount)} currency={t.currency_code} colorize signed className="shrink-0 font-medium" />
              </div>
            ))}
          </div>
        </Panel>
      )}

      <div className="flex items-center justify-between">
        <Button variant="ghost" size="sm" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>Previous</Button>
        <span className="text-xs text-fg-subtle">Page {page + 1}</span>
        <Button variant="ghost" size="sm" disabled={rows.length < limit} onClick={() => setPage((p) => p + 1)}>Next</Button>
      </div>
    </div>
  );
}
