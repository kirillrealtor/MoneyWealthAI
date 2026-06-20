"use client";

import {
  BellRing,
  Wallet,
  Target,
  AlertTriangle,
  Landmark,
  Check,
  CheckCheck,
} from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Dot } from "@/components/ui/badge";
import { useNotifications, useMarkRead, useMarkAllRead } from "@/lib/api/notifications";
import type { Notification } from "@/lib/api/types";
import { cn } from "@/lib/utils";

const ICONS: Record<string, typeof BellRing> = {
  budget_threshold: Wallet,
  budget_overpace: Wallet,
  goal_behind: Target,
  goal_milestone: Target,
  unusual_transaction: AlertTriangle,
  bank_connection_error: Landmark,
  bank_token_expiring: Landmark,
};

export default function NotificationsPage() {
  const { data, isLoading, isError } = useNotifications();
  const markRead = useMarkRead();
  const markAll = useMarkAllRead();
  const items = data?.items ?? [];
  const unread = data?.unread_count ?? 0;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-medium tracking-tight">Notifications</h1>
          <p className="mt-1 text-sm text-fg-muted">
            {unread > 0 ? `${unread} unread` : "You're all caught up."}
          </p>
        </div>
        {unread > 0 && (
          <Button variant="secondary" size="sm" onClick={() => markAll.mutate()} loading={markAll.isPending}>
            <CheckCheck className="size-4" /> Mark all read
          </Button>
        )}
      </div>

      {isLoading && <div className="space-y-3">{[0, 1, 2].map((i) => <div key={i} className="skeleton h-16 w-full" />)}</div>}
      {isError && <Panel className="text-sm text-fg-muted">Couldn&apos;t load notifications.</Panel>}

      {data && items.length === 0 && (
        <Panel className="flex flex-col items-center py-16 text-center">
          <span className="grid size-12 place-items-center rounded-2xl bg-brand/10 ring-1 ring-brand/20">
            <BellRing className="size-6 text-brand" />
          </span>
          <h3 className="mt-4 text-lg font-medium">Nothing yet</h3>
          <p className="mt-1 max-w-xs text-sm text-fg-muted">
            Budget, goal and unusual-charge alerts will appear here as they happen.
          </p>
        </Panel>
      )}

      {items.length > 0 && (
        <div className="space-y-2.5">
          {items.map((n) => (
            <Row key={n.alert_id} n={n} onRead={() => markRead.mutate(n.alert_id)} />
          ))}
        </div>
      )}
    </div>
  );
}

function Row({ n, onRead }: { n: Notification; onRead: () => void }) {
  const Icon = ICONS[n.type] ?? BellRing;
  return (
    <Panel className={cn("group flex items-start gap-3 py-4", !n.is_read && "ring-1 ring-brand/20")}>
      <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-black/5 ring-1 ring-line">
        <Icon className="size-[18px] text-fg-muted" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          {!n.is_read && <Dot tone="positive" />}
          <p className="truncate text-sm font-medium text-fg">{n.title ?? "Alert"}</p>
        </div>
        {n.body && <p className="mt-0.5 text-sm text-fg-muted">{n.body}</p>}
        <p className="mt-1 text-xs text-fg-subtle">
          {new Date(n.created_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}
        </p>
      </div>
      {!n.is_read && (
        <button
          onClick={onRead}
          aria-label="Mark read"
          className="grid size-8 shrink-0 place-items-center rounded-lg text-fg-subtle opacity-0 transition-opacity hover:bg-black/5 hover:text-fg group-hover:opacity-100"
        >
          <Check className="size-4" />
        </button>
      )}
    </Panel>
  );
}
