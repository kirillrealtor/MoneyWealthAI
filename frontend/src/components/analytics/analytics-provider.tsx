"use client";

import { useEffect, useSyncExternalStore } from "react";
import posthog from "posthog-js";
import { Button } from "@/components/ui/button";

/**
 * Privacy-first analytics. PostHog only initialises when BOTH a key is present
 * AND the user has granted consent — so it's a complete no-op until you add
 * NEXT_PUBLIC_POSTHOG_KEY, and never tracks without opt-in. No PII is sent
 * (person_profiles: identified_only; mask inputs in any future session replay).
 */
const KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY;
const HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://us.i.posthog.com";
const CONSENT = "fathom_analytics_consent";

const listeners = new Set<() => void>();
function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => listeners.delete(cb);
}
function getConsent(): string | null {
  return typeof window === "undefined" ? null : localStorage.getItem(CONSENT);
}
function setConsent(value: "granted" | "declined") {
  localStorage.setItem(CONSENT, value);
  listeners.forEach((l) => l());
}
function useConsent() {
  return useSyncExternalStore(subscribe, getConsent, () => null);
}

export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  const consent = useConsent();

  useEffect(() => {
    // init is a side effect (not setState) — safe in an effect.
    if (KEY && consent === "granted" && !posthog.__loaded) {
      posthog.init(KEY, {
        api_host: HOST,
        capture_pageview: true,
        person_profiles: "identified_only",
      });
    }
  }, [consent]);

  return (
    <>
      {children}
      {KEY && consent === null && <ConsentBanner />}
    </>
  );
}

function ConsentBanner() {
  return (
    <div className="fixed inset-x-3 bottom-3 z-50 mx-auto max-w-xl">
      <div className="glass flex flex-col items-center gap-3 rounded-[16px] p-4 text-sm sm:flex-row">
        <p className="flex-1 text-fg-muted">
          We use privacy-friendly analytics to improve Fathom. No financial data is ever sent.
        </p>
        <div className="flex shrink-0 gap-2">
          <Button variant="ghost" size="sm" onClick={() => setConsent("declined")}>
            Decline
          </Button>
          <Button size="sm" onClick={() => setConsent("granted")}>
            Allow
          </Button>
        </div>
      </div>
    </div>
  );
}
