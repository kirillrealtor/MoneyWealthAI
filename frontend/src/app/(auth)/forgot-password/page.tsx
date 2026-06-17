"use client";

import { useState } from "react";
import Link from "next/link";
import { MailCheck } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Input, Field } from "@/components/ui/input";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    // Anti-enumeration: backend always returns the same generic response.
    await fetch("/api/backend/auth/forgot-password", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email }),
    });
    setLoading(false);
    setSent(true);
  }

  if (sent) {
    return (
      <Panel className="p-7 text-center sm:p-8">
        <div className="mx-auto grid size-12 place-items-center rounded-full bg-brand/15 ring-1 ring-brand/30">
          <MailCheck className="size-6 text-brand" />
        </div>
        <h1 className="mt-5 text-2xl font-medium tracking-tight">Check your email</h1>
        <p className="mt-2 text-sm text-fg-muted">
          If an account exists for <span className="text-fg">{email}</span>, we&apos;ve sent a link to
          reset your password. It expires in 1 hour.
        </p>
        <Link href="/login" className="mt-6 block">
          <Button variant="secondary" className="w-full">Back to log in</Button>
        </Link>
      </Panel>
    );
  }

  return (
    <Panel className="p-7 sm:p-8">
      <h1 className="text-2xl font-medium tracking-tight">Reset your password</h1>
      <p className="mt-1.5 text-sm text-fg-muted">Enter your email and we&apos;ll send you a reset link.</p>
      <form onSubmit={onSubmit} className="mt-7 space-y-4" noValidate>
        <Field label="Email" htmlFor="email">
          <Input id="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
        </Field>
        <Button type="submit" className="w-full" size="lg" loading={loading}>Send reset link</Button>
      </form>
      <p className="mt-6 text-center text-sm text-fg-muted">
        <Link href="/login" className="font-medium text-brand hover:underline">Back to log in</Link>
      </p>
    </Panel>
  );
}
