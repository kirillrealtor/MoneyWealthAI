"use client";

import { toast } from "sonner";
import { Panel } from "@/components/ui/panel";
import { Toggle } from "@/components/ui/toggle";
import { useFlags, useSetFlag } from "@/lib/admin/hooks";

export default function AdminFlagsPage() {
  const { data, isLoading, isError } = useFlags();
  const setFlag = useSetFlag();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-medium tracking-tight">Feature flags</h1>
        <p className="mt-1 text-sm text-fg-muted">Toggle platform features without a deploy. Owner only.</p>
      </div>

      {isError && <Panel className="text-sm text-fg-muted">Couldn&apos;t load flags.</Panel>}
      {isLoading && <div className="space-y-2">{[0, 1, 2].map((i) => <div key={i} className="skeleton h-16 w-full" />)}</div>}

      {data && (
        <Panel className="p-0">
          <div className="divide-y divide-line">
            {data.map((f) => (
              <div key={f.key} className="flex items-center justify-between gap-4 px-5 py-4">
                <div className="min-w-0">
                  <p className="font-mono text-sm text-fg">{f.key}</p>
                  {f.description && <p className="mt-0.5 text-xs text-fg-subtle">{f.description}</p>}
                </div>
                <Toggle
                  checked={f.enabled}
                  label={f.key}
                  disabled={setFlag.isPending}
                  onChange={(v) =>
                    setFlag.mutate(
                      { key: f.key, enabled: v },
                      {
                        onSuccess: () => toast.success(`${f.key} ${v ? "enabled" : "disabled"}`),
                        onError: () => toast.error("Couldn't update flag (owner only)."),
                      },
                    )
                  }
                />
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}
