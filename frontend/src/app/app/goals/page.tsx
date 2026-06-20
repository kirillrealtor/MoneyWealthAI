"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Plus, Pencil, Trash2, Target } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Money } from "@/components/ui/money";
import { GoalDialog } from "@/components/goals/goal-dialog";
import { useGoals, useDeleteGoal, useCreateGoal } from "@/lib/api/goals";
import type { Goal } from "@/lib/api/types";

export default function GoalsPage() {
  const { data: goals, isLoading, isError } = useGoals();
  const del = useDeleteGoal();
  const recreate = useCreateGoal();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Goal | null>(null);

  function openNew() {
    setEditing(null);
    setOpen(true);
  }
  function openEdit(g: Goal) {
    setEditing(g);
    setOpen(true);
  }
  async function onDelete(g: Goal) {
    await del.mutateAsync(g.goal_id);
    toast(`"${g.title}" deleted`, {
      action: {
        label: "Undo",
        onClick: () =>
          recreate.mutate({
            title: g.title,
            target_amount: String(Number(g.target_amount)),
            current_amount: String(Number(g.current_amount)),
            target_date: g.target_date,
          }),
      },
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-medium tracking-tight">Goals</h1>
          <p className="mt-1 text-sm text-fg-muted">Save toward what matters, on a clear schedule.</p>
        </div>
        <Button onClick={openNew}>
          <Plus className="size-4" /> New goal
        </Button>
      </div>

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2">
          {[0, 1].map((i) => <div key={i} className="skeleton h-44 w-full" />)}
        </div>
      )}

      {isError && <Panel className="text-sm text-fg-muted">Couldn&apos;t load your goals. Please retry.</Panel>}

      {goals && goals.length === 0 && <EmptyState onNew={openNew} />}

      {goals && goals.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2">
          {goals.map((g) => (
            <GoalCard key={g.goal_id} goal={g} onEdit={openEdit} onDelete={onDelete} />
          ))}
        </div>
      )}

      <GoalDialog open={open} onOpenChange={setOpen} editing={editing} />
    </div>
  );
}

function GoalCard({
  goal: g,
  onEdit,
  onDelete,
}: {
  goal: Goal;
  onEdit: (g: Goal) => void;
  onDelete: (g: Goal) => void;
}) {
  const pct = Math.min(g.progress_pct, 100);
  return (
    <Panel className="group">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <GoalRing pct={pct} />
          <div>
            <p className="font-medium">{g.title}</p>
            <p className="text-xs text-fg-subtle">
              <Money value={g.current_amount} /> of <Money value={g.target_amount} />
            </p>
          </div>
        </div>
        <div className="flex opacity-0 transition-opacity group-hover:opacity-100">
          <button onClick={() => onEdit(g)} aria-label="Edit goal" className="grid size-9 place-items-center rounded-lg text-fg-subtle hover:bg-black/5 hover:text-fg">
            <Pencil className="size-4" />
          </button>
          <button onClick={() => onDelete(g)} aria-label="Delete goal" className="grid size-9 place-items-center rounded-lg text-fg-subtle hover:bg-negative/10 hover:text-negative">
            <Trash2 className="size-4" />
          </button>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <div className="text-sm">
          <span className="text-fg-subtle">Monthly target</span>{" "}
          <span className="font-medium text-fg">
            {g.monthly_target ? <Money value={g.monthly_target} /> : "—"}
          </span>
        </div>
        {g.status === "completed" ? (
          <Badge tone="brand">Completed</Badge>
        ) : g.on_track ? (
          <Badge tone="positive">On track</Badge>
        ) : (
          <Badge tone="warning">Behind</Badge>
        )}
      </div>
      <p className="mt-2 text-xs text-fg-subtle">
        Target by {new Date(g.target_date).toLocaleDateString("en-US", { month: "short", year: "numeric" })}
      </p>
    </Panel>
  );
}

function GoalRing({ pct }: { pct: number }) {
  const r = 24;
  const c = 2 * Math.PI * r;
  return (
    <svg viewBox="0 0 60 60" className="size-14 -rotate-90" aria-hidden>
      <circle cx="30" cy="30" r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="5" />
      <circle
        cx="30" cy="30" r={r} fill="none" stroke="url(#goalgrad)" strokeWidth="5" strokeLinecap="round"
        strokeDasharray={c} strokeDashoffset={c * (1 - pct / 100)}
      />
      <defs>
        <linearGradient id="goalgrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#0e9f6e" />
          <stop offset="1" stopColor="#14b8a6" />
        </linearGradient>
      </defs>
      <text x="30" y="31" transform="rotate(90 30 30)" textAnchor="middle" dominantBaseline="middle" className="fill-fg text-[12px] font-medium tnum">
        {Math.round(pct)}%
      </text>
    </svg>
  );
}

function EmptyState({ onNew }: { onNew: () => void }) {
  return (
    <Panel className="flex flex-col items-center py-14 text-center">
      <span className="grid size-12 place-items-center rounded-2xl bg-iris/10 ring-1 ring-iris/20">
        <Target className="size-6 text-iris" />
      </span>
      <h3 className="mt-4 text-lg font-medium">No goals yet</h3>
      <p className="mt-1 max-w-xs text-sm text-fg-muted">
        Name a target and date — we&apos;ll work out the monthly amount to get you there.
      </p>
      <Button className="mt-5" onClick={onNew}>
        <Plus className="size-4" /> Create your first goal
      </Button>
    </Panel>
  );
}
