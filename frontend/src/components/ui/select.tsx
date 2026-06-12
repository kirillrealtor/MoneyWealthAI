"use client";

import * as React from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

/** Styled native <select> — fully accessible, no JS overhead. */
export const Select = React.forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement> & { invalid?: boolean }
>(({ className, invalid, children, ...props }, ref) => (
  <div className="relative">
    <select
      ref={ref}
      aria-invalid={invalid || undefined}
      className={cn(
        "h-11 w-full appearance-none rounded-[12px] border bg-surface/60 px-3.5 pr-10 text-sm text-fg",
        "outline-none transition-all duration-200",
        "border-line focus:border-brand/50 focus:ring-2 focus:ring-brand/25",
        "aria-[invalid]:border-negative/60",
        "[&>option]:bg-surface-2 [&>option]:text-fg",
        className,
      )}
      {...props}
    >
      {children}
    </select>
    <ChevronDown className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-fg-subtle" />
  </div>
));
Select.displayName = "Select";
