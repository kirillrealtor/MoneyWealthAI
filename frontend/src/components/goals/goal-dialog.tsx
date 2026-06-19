"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input, Field } from "@/components/ui/input";
import { MoneyInput } from "@/components/ui/money-input";
import type { Goal } from "@/lib/api/types";
import { useCreateGoal, useUpdateGoal } from "@/lib/api/goals";
import { ApiRequestError } from "@/lib/api/client";
import { amountSchema, validate } from "@/lib/validation";

function tomorrowISO() {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().slice(0, 10);
}

export function GoalDialog({
  open,
  onOpenChange,
  editing,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  editing?: Goal | null;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        title={editing ? "Edit goal" : "New goal"}
        description={editing ? undefined : "We'll reverse-engineer the monthly amount you need."}
      >
        <GoalForm key={editing?.goal_id ?? "new"} editing={editing} onDone={() => onOpenChange(false)} />
      </DialogContent>
    </Dialog>
  );
}

function GoalForm({ editing, onDone }: { editing?: Goal | null; onDone: () => void }) {
  const create = useCreateGoal();
  const update = useUpdateGoal();
  const isEdit = !!editing;

  const [title, setTitle] = useState(editing?.title ?? "");
  const [target, setTarget] = useState(editing ? String(Number(editing.target_amount)) : "");
  const [current, setCurrent] = useState(editing ? String(Number(editing.current_amount)) : "");
  const [date, setDate] = useState(editing?.target_date ?? "");
  const [error, setError] = useState<string | null>(null);
  const [targetError, setTargetError] = useState<string | null>(null);

  const pending = create.isPending || update.isPending;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setTargetError(null);
    if (!title.trim()) return setError("Give your goal a name.");
    const amt = validate(amountSchema, target);
    if (!amt.ok) {
      setTargetError(Object.values(amt.errors)[0] ?? "Enter a valid target amount.");
      return;
    }
    if (!date) return setError("Pick a target date.");
    if (date <= new Date().toISOString().slice(0, 10)) return setError("Target date must be in the future.");

    try {
      const payload = { title: title.trim(), target_amount: target, target_date: date, current_amount: current || "0" };
      if (isEdit && editing) {
        await update.mutateAsync({ id: editing.goal_id, ...payload });
        toast.success("Goal updated");
      } else {
        await create.mutateAsync(payload);
        toast.success("Goal created");
      }
      onDone();
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.payload.message : "Something went wrong.");
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4" noValidate>
      {error && (
        <div role="alert" className="rounded-[12px] border border-negative/30 bg-negative/10 px-3.5 py-2.5 text-sm text-negative">
          {error}
        </div>
      )}

      <Field label="Goal name" htmlFor="title">
        <Input id="title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Emergency Fund" maxLength={255} />
      </Field>

      <div className="grid grid-cols-2 gap-3">
        <Field label="Target amount" htmlFor="target">
          <MoneyInput
            id="target"
            value={target}
            onChange={(v) => {
              setTarget(v);
              setTargetError(null);
            }}
            invalid={!!targetError}
          />
          {targetError && <p className="mt-1.5 text-xs text-negative">{targetError}</p>}
        </Field>
        <Field label="Saved so far" htmlFor="current">
          <MoneyInput id="current" value={current} onChange={setCurrent} placeholder="0.00" />
        </Field>
      </div>

      <Field label="Target date" htmlFor="date">
        <Input
          id="date"
          type="date"
          min={tomorrowISO()}
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="[color-scheme:dark]"
        />
      </Field>

      <div className="flex justify-end gap-2 pt-1">
        <Button type="button" variant="ghost" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" loading={pending}>
          {isEdit ? "Save changes" : "Create goal"}
        </Button>
      </div>
    </form>
  );
}
