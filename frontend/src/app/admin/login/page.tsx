"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input, PasswordInput, Field } from "@/components/ui/input";
import { useAdmin } from "@/lib/admin/context";

export default function AdminLoginPage() {
  const router = useRouter();
  const { login } = useAdmin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const res = await login(email, password);
    setLoading(false);
    if (res.ok) router.push("/admin");
    else setError(res.error.code === "RATE_LIMITED" ? "Too many attempts. Wait a minute." : "Invalid email or password.");
  }

  return (
    <div className="grid min-h-dvh place-items-center px-5">
      <div className="w-full max-w-sm rounded-[18px] border border-line bg-surface/60 p-7 backdrop-blur-xl">
        <div className="flex items-center gap-2 text-fg-subtle">
          <ShieldCheck className="size-5 text-iris" />
          <span className="text-xs font-medium uppercase tracking-[0.2em]">Admin console</span>
        </div>
        <h1 className="mt-4 text-xl font-medium tracking-tight">Staff sign-in</h1>
        <p className="mt-1 text-sm text-fg-muted">Authorized personnel only. All actions are audited.</p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
          {error && (
            <div role="alert" className="rounded-[12px] border border-negative/30 bg-negative/10 px-3.5 py-2.5 text-sm text-negative">
              {error}
            </div>
          )}
          <Field label="Email" htmlFor="email">
            <Input id="email" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </Field>
          <Field label="Password" htmlFor="password">
            <PasswordInput id="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </Field>
          <Button type="submit" className="w-full" size="lg" loading={loading}>Sign in</Button>
        </form>
      </div>
    </div>
  );
}
