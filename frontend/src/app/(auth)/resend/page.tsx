"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Input, Field } from "@/components/ui/input";
import { isMagicLinkAuth } from "@/lib/auth/mode";

export default function ResendPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  useEffect(() => {
    if (isMagicLinkAuth()) router.replace("/login");
  }, [router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    await fetch("/api/auth/resend-verification", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email }),
    });
    setLoading(false);
    setSent(true);
  }

  if (isMagicLinkAuth()) return null;

  return (
    <Panel className="p-7 sm:p-8">
      <h1 className="text-2xl font-medium tracking-tight">Resend verification</h1>
      <p className="mt-1.5 text-sm text-fg-muted">
        Enter your email and we&apos;ll send a fresh link if an unverified account exists.
      </p>

      {sent ? (
        <div className="mt-6 rounded-[12px] border border-brand/30 bg-brand/10 px-4 py-3 text-sm text-fg">
          If an unverified account exists for <span className="font-medium">{email}</span>, a new
          link is on its way.
        </div>
      ) : (
        <form onSubmit={onSubmit} className="mt-7 space-y-4" noValidate>
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
          <Button type="submit" className="w-full" size="lg" loading={loading}>
            Send link
          </Button>
        </form>
      )}

      <p className="mt-6 text-center text-sm text-fg-muted">
        <Link href="/login" className="font-medium text-brand hover:underline">
          Back to log in
        </Link>
      </p>
    </Panel>
  );
}
