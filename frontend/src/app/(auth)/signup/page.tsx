"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { MailCheck } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Input, PasswordInput, Field } from "@/components/ui/input";
import { GoogleAuthSection } from "@/components/auth/google-button";
import { isMagicLinkAuth } from "@/lib/auth/mode";
import { signupSchema, validate } from "@/lib/validation";
import type { ApiError } from "@/lib/auth/types";

function strength(pw: string): { score: number; label: string } {
  let s = 0;
  if (pw.length >= 8) s++;
  if (pw.length >= 12) s++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
  if (/\d/.test(pw)) s++;
  if (/[^A-Za-z0-9]/.test(pw)) s++;
  const label = ["Too short", "Weak", "Fair", "Good", "Strong", "Strong"][s];
  return { score: s, label };
}

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [exists, setExists] = useState(false);

  useEffect(() => {
    if (isMagicLinkAuth()) router.replace("/login");
  }, [router]);

  const pw = strength(password);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setFieldErrors({});
    setExists(false);
    const check = validate(signupSchema, { email, password });
    if (!check.ok) {
      setFieldErrors(check.errors);
      return;
    }
    setLoading(true);
    const res = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    setLoading(false);

    if (res.ok) {
      setDone(true);
      return;
    }
    const err = data as ApiError;
    if (err.code === "CONFLICT") {
      setExists(true);
    } else if (err.code === "VALIDATION_ERROR" && err.details?.length) {
      const fe: Record<string, string> = {};
      for (const d of err.details) {
        const key = d.loc?.[d.loc.length - 1];
        if (typeof key === "string" && d.msg) fe[key] = d.msg;
      }
      setFieldErrors(fe);
    } else {
      setError(err.message || "Something went wrong. Please try again.");
    }
  }

  if (isMagicLinkAuth()) return null;

  if (done) {
    return (
      <Panel className="p-7 text-center sm:p-8">
        <div className="mx-auto grid size-12 place-items-center rounded-full bg-brand/15 ring-1 ring-brand/30">
          <MailCheck className="size-6 text-brand" />
        </div>
        <h1 className="mt-5 text-2xl font-medium tracking-tight">Check your email</h1>
        <p className="mt-2 text-sm text-fg-muted">
          We sent a verification link to <span className="text-fg">{email}</span>. Click it to
          activate your account, then log in.
        </p>
        <Link href="/login" className="mt-6 block">
          <Button variant="secondary" className="w-full">
            Back to log in
          </Button>
        </Link>
      </Panel>
    );
  }

  return (
    <Panel className="p-7 sm:p-8">
      <h1 className="text-2xl font-medium tracking-tight">Create your account</h1>
      <p className="mt-1.5 text-sm text-fg-muted">Free to start — no card required.</p>

      <form onSubmit={onSubmit} className="mt-7 space-y-4" noValidate>
        {error && (
          <div
            role="alert"
            className="rounded-[12px] border border-negative/30 bg-negative/10 px-3.5 py-2.5 text-sm text-negative"
          >
            {error}
          </div>
        )}

        {exists && (
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-[12px] border border-brand/30 bg-brand/10 px-3.5 py-2.5 text-sm text-fg">
            <span>This email already has an account.</span>
            <Link
              href={`/login?email=${encodeURIComponent(email)}`}
              className="font-medium text-brand hover:underline"
            >
              Log in instead →
            </Link>
          </div>
        )}

        <Field label="Email" htmlFor="email" error={fieldErrors.email}>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            invalid={!!fieldErrors.email || exists}
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              setExists(false);
            }}
            placeholder="you@example.com"
          />
        </Field>

        <Field
          label="Password"
          htmlFor="password"
          error={fieldErrors.password}
          hint={password ? undefined : "At least 8 characters."}
        >
          <PasswordInput
            id="password"
            autoComplete="new-password"
            required
            invalid={!!fieldErrors.password}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Create a strong password"
          />
          {password && (
            <div className="mt-2 flex items-center gap-2">
              <div className="flex flex-1 gap-1">
                {[0, 1, 2, 3].map((i) => (
                  <span
                    key={i}
                    className={`h-1 flex-1 rounded-full transition-colors ${
                      i < pw.score
                        ? pw.score <= 2
                          ? "bg-warning"
                          : "bg-positive"
                        : "bg-hover-strong"
                    }`}
                  />
                ))}
              </div>
              <span className="text-xs text-fg-subtle">{pw.label}</span>
            </div>
          )}
        </Field>

        <Button type="submit" className="w-full" size="lg" loading={loading}>
          Create account
        </Button>

        <p className="text-center text-xs text-fg-subtle">
          By continuing you agree to our Terms and acknowledge our Privacy Policy.
        </p>
      </form>

      <GoogleAuthSection />

      <p className="mt-5 text-center text-sm text-fg-muted">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-brand hover:underline">
          Log in
        </Link>
      </p>
    </Panel>
  );
}
