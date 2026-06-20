import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badge = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
  {
    variants: {
      tone: {
        brand: "bg-brand/12 text-brand ring-1 ring-brand/25",
        neutral: "bg-black/5 text-fg-muted ring-1 ring-line",
        positive: "bg-positive/12 text-positive ring-1 ring-positive/25",
        negative: "bg-negative/12 text-negative ring-1 ring-negative/25",
        warning: "bg-warning/12 text-warning ring-1 ring-warning/25",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
);

export function Badge({
  className,
  tone,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badge>) {
  return <span className={cn(badge({ tone }), className)} {...props} />;
}

/** Tiny status dot. */
export function Dot({ tone = "positive", className }: { tone?: "positive" | "warning" | "negative" | "neutral"; className?: string }) {
  const map = {
    positive: "bg-positive",
    warning: "bg-warning",
    negative: "bg-negative",
    neutral: "bg-neutral",
  };
  return (
    <span className={cn("relative inline-flex size-2", className)}>
      <span className={cn("absolute inline-flex h-full w-full animate-ping rounded-full opacity-60", map[tone])} />
      <span className={cn("relative inline-flex size-2 rounded-full", map[tone])} />
    </span>
  );
}
