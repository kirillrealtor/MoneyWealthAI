"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";

type State = "verifying" | "success" | "error";

function VerifyInner() {
  const token = useSearchParams().get("token");
  // Derive the no-token case at init so we never setState synchronously in the effect.
  const [state, setState] = useState<State>(token ? "verifying" : "error");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      const res = await fetch(`/api/auth/verify-email?token=${encodeURIComponent(token)}`);
      if (cancelled) return;
      setState(res.ok ? "success" : "error");
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  if (state === "verifying") {
    return (
      <Panel className="p-8 text-center">
        <Loader2 className="mx-auto size-8 animate-spin text-brand" />
        <p className="mt-4 text-sm text-fg-muted">Verifying your email…</p>
      </Panel>
    );
  }

  if (state === "success") {
    return (
      <Panel className="p-8 text-center">
        <div className="mx-auto grid size-12 place-items-center rounded-full bg-positive/15 ring-1 ring-positive/30">
          <CheckCircle2 className="size-6 text-positive" />
        </div>
        <h1 className="mt-5 text-2xl font-medium tracking-tight">Email verified</h1>
        <p className="mt-2 text-sm text-fg-muted">Your account is active. You can log in now.</p>
        <Link href="/login" className="mt-6 block">
          <Button className="w-full">Continue to log in</Button>
        </Link>
      </Panel>
    );
  }

  return (
    <Panel className="p-8 text-center">
      <div className="mx-auto grid size-12 place-items-center rounded-full bg-negative/15 ring-1 ring-negative/30">
        <XCircle className="size-6 text-negative" />
      </div>
      <h1 className="mt-5 text-2xl font-medium tracking-tight">Link expired or invalid</h1>
      <p className="mt-2 text-sm text-fg-muted">
        This verification link is no longer valid. Request a fresh one.
      </p>
      <Link href="/resend" className="mt-6 block">
        <Button variant="secondary" className="w-full">
          Resend verification
        </Button>
      </Link>
    </Panel>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <Panel className="p-8 text-center">
          <Loader2 className="mx-auto size-8 animate-spin text-brand" />
        </Panel>
      }
    >
      <VerifyInner />
    </Suspense>
  );
}
