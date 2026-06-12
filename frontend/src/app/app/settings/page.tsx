"use client";

import { toast } from "sonner";
import { Panel, PanelHeader } from "@/components/ui/panel";
import { Badge } from "@/components/ui/badge";
import { Toggle } from "@/components/ui/toggle";
import { Input, Field } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useAuth } from "@/lib/auth/context";
import { usePreferences, useUpdatePreferences } from "@/lib/api/notifications";
import type { Preferences } from "@/lib/api/types";

const TIMEZONES = [
  "UTC", "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
  "Europe/London", "Europe/Berlin", "Asia/Karachi", "Asia/Dubai", "Asia/Kolkata", "Asia/Tokyo",
];

export default function SettingsPage() {
  const { user } = useAuth();
  const { data: prefs, isLoading } = usePreferences();
  const update = useUpdatePreferences();

  function patch(p: Partial<Preferences>) {
    update.mutate(p, {
      onError: () => toast.error("Couldn't save — please retry."),
    });
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-medium tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-fg-muted">Manage your profile and notifications.</p>
      </div>

      {/* Profile */}
      <Panel>
        <PanelHeader title="Profile" hint="Your account details" />
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Email" htmlFor="email">
            <Input id="email" value={user?.email ?? ""} disabled readOnly />
          </Field>
          <Field label="Name" htmlFor="name">
            <Input id="name" value={user?.full_name ?? ""} placeholder="Not set" disabled readOnly />
          </Field>
        </div>
        <div className="mt-4 flex items-center gap-2">
          <Badge tone={user?.tier === "free" ? "neutral" : "brand"}>{user?.tier ?? "free"} plan</Badge>
          {user?.is_verified && <Badge tone="positive">Verified</Badge>}
        </div>
      </Panel>

      {/* Notifications */}
      <Panel>
        <PanelHeader title="Notifications" hint="Choose what reaches you, and when" />
        {isLoading || !prefs ? (
          <div className="space-y-3">{[0, 1, 2].map((i) => <div key={i} className="skeleton h-10 w-full" />)}</div>
        ) : (
          <div className="divide-y divide-line">
            <ToggleRow label="Budget alerts" desc="Overspend and pace warnings" checked={prefs.budget_alerts} onChange={(v) => patch({ budget_alerts: v })} />
            <ToggleRow label="Goal alerts" desc="Milestones and behind-pace nudges" checked={prefs.goal_alerts} onChange={(v) => patch({ goal_alerts: v })} />
            <ToggleRow label="Unusual transactions" desc="Larger-than-normal charges" checked={prefs.unusual_tx_alerts} onChange={(v) => patch({ unusual_tx_alerts: v })} />
            <ToggleRow label="Bank connection errors" desc="When a linked account needs attention" checked={prefs.bank_error_alerts} onChange={(v) => patch({ bank_error_alerts: v })} />
            <ToggleRow label="Email notifications" desc="Receive alerts by email" checked={prefs.email_enabled} onChange={(v) => patch({ email_enabled: v })} />
            <ToggleRow label="Weekly digest" desc="A Sunday summary of your week" checked={prefs.weekly_digest} onChange={(v) => patch({ weekly_digest: v })} />
            <ToggleRow label="SMS (carrier rates apply)" desc="Opt in to text alerts (TCPA)" checked={prefs.sms_opt_in} onChange={(v) => patch({ sms_opt_in: v })} />
          </div>
        )}
      </Panel>

      {/* Quiet hours */}
      {prefs && (
        <Panel>
          <PanelHeader title="Quiet hours" hint="Push & SMS are held during this window" />
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="From" htmlFor="qfrom">
              <Input id="qfrom" type="time" value={prefs.quiet_hours_start.slice(0, 5)} onChange={(e) => patch({ quiet_hours_start: `${e.target.value}:00` })} className="[color-scheme:dark]" />
            </Field>
            <Field label="To" htmlFor="qto">
              <Input id="qto" type="time" value={prefs.quiet_hours_end.slice(0, 5)} onChange={(e) => patch({ quiet_hours_end: `${e.target.value}:00` })} className="[color-scheme:dark]" />
            </Field>
            <Field label="Timezone" htmlFor="tz">
              <Select id="tz" value={prefs.timezone} onChange={(e) => patch({ timezone: e.target.value })}>
                {TIMEZONES.includes(prefs.timezone) ? null : <option value={prefs.timezone}>{prefs.timezone}</option>}
                {TIMEZONES.map((tz) => <option key={tz} value={tz}>{tz}</option>)}
              </Select>
            </Field>
          </div>
        </Panel>
      )}
    </div>
  );
}

function ToggleRow({
  label,
  desc,
  checked,
  onChange,
}: {
  label: string;
  desc: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-3.5">
      <div>
        <p className="text-sm font-medium text-fg">{label}</p>
        <p className="text-xs text-fg-subtle">{desc}</p>
      </div>
      <Toggle checked={checked} onChange={onChange} label={label} />
    </div>
  );
}
