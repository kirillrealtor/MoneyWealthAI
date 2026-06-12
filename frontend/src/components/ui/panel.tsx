import * as React from "react";
import { cn } from "@/lib/utils";

/** Glass surface — the core container of the product. */
export function Panel({
  className,
  interactive,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { interactive?: boolean }) {
  return (
    <div
      className={cn(
        "glass rounded-[18px] p-5 transition-all duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)]",
        interactive && "hover:ring-glow hover:-translate-y-0.5 cursor-pointer",
        className,
      )}
      {...props}
    />
  );
}

export function PanelHeader({
  title,
  hint,
  action,
  className,
}: {
  title: React.ReactNode;
  hint?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mb-4 flex items-start justify-between gap-3", className)}>
      <div>
        <h3 className="text-sm font-medium text-fg">{title}</h3>
        {hint && <p className="mt-0.5 text-xs text-fg-subtle">{hint}</p>}
      </div>
      {action}
    </div>
  );
}
