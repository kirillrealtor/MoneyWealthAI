"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { CheckCircle2 } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { PasswordInput, Field } from "@/components/ui/input";
import { isMagicLinkAuth } from "@/lib/auth/mode";

function ResetForm() {
  const router = useRouter();
  const token = useSearchParams().get("token") ?? "";
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (isMagicLinkAuth()) router.replace("/login");
  }, [router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) return setError("Use at least 8 characters.");
    if (!token) return setError("This reset link is invalid.");
    setLoading(true);
    const res = await fetch("/api/backend/auth/reset-password", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ token, password }),
    });
    setLoading(false);
    if (res.ok) {
      setDone(true);
      setTimeout(() => router.push("/login"), 1500);
    } else {
      const data = await res.json().catch(() => ({}));
      setError(
        data?.code === "VALIDATION_ERROR"
          ? "This reset link is invalid or expired."
          : "Something went wrong.",
      );
    }
  }

  if (isMagicLinkAuth()) return null;

  if (done) {
    return (
      <Panel className="p-8 text-center">
        <div className="mx-auto grid size-12 place-items-center rounded-full bg-positive/15 ring-1 ring-positive/30">
          <CheckCircle2 className="size-6 text-positive" />
        </div>
        <h1 className="mt-5 text-2xl font-medium tracking-tight">Password updated</h1>
        <p className="mt-2 text-sm text-fg-muted">Taking you to log in…</p>
      </Panel>
    );
  }

  return (
    <Panel className="p-7 sm:p-8">
      <h1 className="text-2xl font-medium tracking-tight">Choose a new password</h1>
      <p className="mt-1.5 text-sm text-fg-muted">For security, this signs out all your sessions.</p>
      <form onSubmit={onSubmit} className="mt-7 space-y-4" noValidate>
        {error && (
          <div
            role="alert"
            className="rounded-[12px] border border-negative/30 bg-negative/10 px-3.5 py-2.5 text-sm text-negative"
          >
            {error}
          </div>
        )}
        <Field label="New password" htmlFor="password" hint="At least 8 characters.">
          <PasswordInput
            id="password"
            autoComplete="new-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Create a strong password"
          />
        </Field>
        <Button type="submit" className="w-full" size="lg" loading={loading}>
          Update password
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-fg-muted">
        <Link href="/login" className="font-medium text-brand hover:underline">
          Back to log in
        </Link>
      </p>
    </Panel>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<Panel className="p-8" />}>
      <ResetForm />
    </Suspense>
  );
}
