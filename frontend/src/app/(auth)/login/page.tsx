"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { MailCheck } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Input, PasswordInput, Field } from "@/components/ui/input";
import { GoogleAuthSection } from "@/components/auth/google-button";
import { useAuth } from "@/lib/auth/context";
import { isMagicLinkAuth } from "@/lib/auth/mode";
import { emailSchema, validate } from "@/lib/validation";
import type { ApiError } from "@/lib/auth/types";

function humanError(e: ApiError): string {
  switch (e.code) {
    case "UNAUTHORIZED":
      return "Invalid email or password.";
    case "FORBIDDEN":
      return "Please verify your email first — check your inbox.";
    case "RATE_LIMITED":
      return "Too many attempts. Please wait a minute and try again.";
    case "CAPTCHA_REQUIRED":
      return "Extra verification needed. Please try again.";
    default:
      return e.message || "Something went wrong. Please try again.";
  }
}

export default function LoginPage() {
  return (
    <Suspense fallback={<Panel className="p-8" />}>
      {isMagicLinkAuth() ? <MagicLinkLoginForm /> : <PasswordLoginForm />}
    </Suspense>
  );
}

function PasswordLoginForm() {
  const router = useRouter();
  const { login } = useAuth();
  const prefill = useSearchParams().get("email") ?? "";
  const [email, setEmail] = useState(prefill);
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const res = await login(email, password);
    setLoading(false);
    if (res.ok) {
      router.push("/app");
    } else {
      setError(humanError(res.error));
    }
  }

  return (
    <Panel className="p-7 sm:p-8">
      <h1 className="text-2xl font-medium tracking-tight">Welcome back</h1>
      <p className="mt-1.5 text-sm text-fg-muted">Log in to your MoneyWealth AI account.</p>

      <form onSubmit={onSubmit} className="mt-7 space-y-4" noValidate>
        {error && (
          <div
            role="alert"
            className="rounded-[12px] border border-negative/30 bg-negative/10 px-3.5 py-2.5 text-sm text-negative"
          >
            {error}
          </div>
        )}

        <Field label="Email" htmlFor="email">
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </Field>

        <Field label="Password" htmlFor="password">
          <PasswordInput
            id="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />
        </Field>

        <div className="text-right">
          <Link href="/forgot-password" className="text-xs text-fg-muted hover:text-fg">
            Forgot password?
          </Link>
        </div>

        <Button type="submit" className="w-full" size="lg" loading={loading}>
          Log in
        </Button>
      </form>

      <GoogleAuthSection />

      <p className="mt-6 text-center text-sm text-fg-muted">
        New to MoneyWealth AI?{" "}
        <Link href="/signup" className="font-medium text-brand hover:underline">
          Create an account
        </Link>
      </p>
    </Panel>
  );
}

function MagicLinkLoginForm() {
  const prefill = useSearchParams().get("email") ?? "";
  const [email, setEmail] = useState(prefill);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setFieldErrors({});
    const check = validate(emailSchema, email);
    if (!check.ok) {
      setFieldErrors({ email: check.errors._ ?? "Enter a valid email address" });
      return;
    }
    setLoading(true);
    const res = await fetch("/api/auth/magic-link", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email }),
    });
    const data = await res.json();
    setLoading(false);

    if (res.ok) {
      setSent(true);
      return;
    }
    setError(humanError(data as ApiError));
  }

  if (sent) {
    return (
      <Panel className="p-7 text-center sm:p-8">
        <div className="mx-auto grid size-12 place-items-center rounded-full bg-brand/15 ring-1 ring-brand/30">
          <MailCheck className="size-6 text-brand" />
        </div>
        <h1 className="mt-5 text-2xl font-medium tracking-tight">Check your email</h1>
        <p className="mt-2 text-sm text-fg-muted">
          We sent a sign-in link to <span className="text-fg">{email}</span>. Click it to continue.
        </p>
        <Button variant="secondary" className="mt-6 w-full" onClick={() => setSent(false)}>
          Use a different email
        </Button>
      </Panel>
    );
  }

  return (
    <Panel className="p-7 sm:p-8">
      <h1 className="text-2xl font-medium tracking-tight">Sign in to MoneyWealth AI</h1>
      <p className="mt-1.5 text-sm text-fg-muted">
        Enter your email and we&apos;ll send you a sign-in link.
      </p>

      <form onSubmit={onSubmit} className="mt-7 space-y-4" noValidate>
        {error && (
          <div
            role="alert"
            className="rounded-[12px] border border-negative/30 bg-negative/10 px-3.5 py-2.5 text-sm text-negative"
          >
            {error}
          </div>
        )}

        <Field label="Email" htmlFor="email" error={fieldErrors.email}>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            invalid={!!fieldErrors.email}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </Field>

        <Button type="submit" className="w-full" size="lg" loading={loading}>
          Continue
        </Button>

        <p className="text-center text-xs text-fg-subtle">
          By continuing you agree to our Terms and acknowledge our Privacy Policy.
        </p>
      </form>

      <GoogleAuthSection />
    </Panel>
  );
}
