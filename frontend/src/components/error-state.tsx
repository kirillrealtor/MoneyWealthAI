"use client";

import { useEffect } from "react";
import { AlertTriangle, RotateCw } from "lucide-react";
import { Button } from "@/components/ui/button";

/** Shared recoverable error UI for route-segment error boundaries. */
export function ErrorState({
  error,
  reset,
  compact,
}: {
  error: Error & { digest?: string };
  reset: () => void;
  compact?: boolean;
}) {
  useEffect(() => {
    // Surface to monitoring in production; never expose internals to the user.
    console.error(error);
  }, [error]);

  return (
    <div className={compact ? "grid place-items-center py-20" : "grid min-h-dvh place-items-center px-5"}>
      <div className="max-w-sm text-center">
        <span className="mx-auto grid size-12 place-items-center rounded-2xl bg-warning/10 ring-1 ring-warning/20">
          <AlertTriangle className="size-6 text-warning" />
        </span>
        <h1 className="mt-5 text-xl font-medium tracking-tight">Something went wrong</h1>
        <p className="mt-2 text-sm text-fg-muted">
          A part of the page failed to load. You can retry — the rest of the app keeps working.
        </p>
        <div className="mt-6 flex justify-center">
          <Button onClick={reset}>
            <RotateCw className="size-4" /> Try again
          </Button>
        </div>
      </div>
    </div>
  );
}
