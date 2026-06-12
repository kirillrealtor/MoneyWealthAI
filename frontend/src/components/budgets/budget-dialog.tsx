"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { MoneyInput } from "@/components/ui/money-input";
import { PLAID_CATEGORIES, categoryLabel, type Budget } from "@/lib/api/types";
import { useCreateBudget, useUpdateBudget } from "@/lib/api/budgets";
import { ApiRequestError } from "@/lib/api/client";

export function BudgetDialog({
  open,
  onOpenChange,
  editing,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  editing?: Budget | null;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        title={editing ? "Edit budget" : "New budget"}
        description={editing ? undefined : "Set a monthly limit for a spending category."}
      >
        {/* key remounts the form with fresh initial state per open/target —
            avoids syncing props into state via an effect. */}
        <BudgetForm key={editing?.budget_id ?? "new"} editing={editing} onDone={() => onOpenChange(false)} />
      </DialogContent>
    </Dialog>
  );
}

function BudgetForm({ editing, onDone }: { editing?: Budget | null; onDone: () => void }) {
  const create = useCreateBudget();
  const update = useUpdateBudget();
  const isEdit = !!editing;

  const [category, setCategory] = useState<string>(editing?.category ?? PLAID_CATEGORIES[0]);
  const [limit, setLimit] = useState(editing ? String(Number(editing.monthly_limit)) : "");
  const [alertPct, setAlertPct] = useState(editing?.alert_at_pct ?? 80);
  const [error, setError] = useState<string | null>(null);

  const pending = create.isPending || update.isPending;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!limit || Number(limit) <= 0) {
      setError("Enter a monthly limit greater than $0.");
      return;
    }
    try {
      if (isEdit && editing) {
        await update.mutateAsync({ id: editing.budget_id, monthly_limit: limit, alert_at_pct: alertPct });
        toast.success(`${categoryLabel(category)} budget updated`);
      } else {
        await create.mutateAsync({ category, monthly_limit: limit, alert_at_pct: alertPct });
        toast.success(`${categoryLabel(category)} budget created`);
      }
      onDone();
    } catch (err) {
      if (err instanceof ApiRequestError && err.payload.code === "CONFLICT") {
        setError("You already have a budget for this category.");
      } else if (err instanceof ApiRequestError) {
        setError(err.payload.message);
      } else {
        setError("Something went wrong. Please try again.");
      }
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4" noValidate>
      {error && (
        <div role="alert" className="rounded-[12px] border border-negative/30 bg-negative/10 px-3.5 py-2.5 text-sm text-negative">
          {error}
        </div>
      )}

      <Field label="Category" htmlFor="category">
        <Select id="category" value={category} onChange={(e) => setCategory(e.target.value)} disabled={isEdit}>
          {PLAID_CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {categoryLabel(c)}
            </option>
          ))}
        </Select>
      </Field>

      <Field label="Monthly limit" htmlFor="limit">
        <MoneyInput id="limit" value={limit} onChange={setLimit} />
      </Field>

      <Field label="Alert me at" htmlFor="alert" hint={`${alertPct}% of the limit`}>
        <input
          id="alert"
          type="range"
          min={1}
          max={100}
          value={alertPct}
          onChange={(e) => setAlertPct(Number(e.target.value))}
          className="w-full accent-[var(--color-brand)]"
        />
      </Field>

      <div className="flex justify-end gap-2 pt-1">
        <Button type="button" variant="ghost" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" loading={pending}>
          {isEdit ? "Save changes" : "Create budget"}
        </Button>
      </div>
    </form>
  );
}
