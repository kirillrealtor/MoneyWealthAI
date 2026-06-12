"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { MONEY_MAX } from "@/lib/api/types";

/**
 * Money input — emits a decimal STRING (never a float). Enforces the backend's
 * NUMERIC(10,2) ceiling client-side so the user is stopped before the round-trip
 * (mirrors the backend MONEY_MAX cap).
 */
export function MoneyInput({
  value,
  onChange,
  invalid,
  id,
  placeholder = "0.00",
  className,
}: {
  value: string;
  onChange: (v: string) => void;
  invalid?: boolean;
  id?: string;
  placeholder?: string;
  className?: string;
}) {
  function handle(e: React.ChangeEvent<HTMLInputElement>) {
    let raw = e.target.value.replace(/[^0-9.]/g, "");
    const firstDot = raw.indexOf(".");
    if (firstDot !== -1) {
      // keep a single dot, max 2 decimals
      raw =
        raw.slice(0, firstDot + 1) +
        raw.slice(firstDot + 1).replace(/\./g, "").slice(0, 2);
    }
    if (raw && Number(raw) > MONEY_MAX) return; // hard cap
    onChange(raw);
  }

  return (
    <div className="relative">
      <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-sm text-fg-subtle">
        $
      </span>
      <input
        id={id}
        inputMode="decimal"
        value={value}
        onChange={handle}
        placeholder={placeholder}
        aria-invalid={invalid || undefined}
        className={cn(
          "h-11 w-full rounded-[12px] border bg-surface/60 pl-7 pr-3.5 text-sm tabular-nums text-fg placeholder:text-fg-subtle",
          "outline-none transition-all duration-200",
          "border-line focus:border-brand/50 focus:ring-2 focus:ring-brand/25",
          "aria-[invalid]:border-negative/60",
          className,
        )}
      />
    </div>
  );
}
