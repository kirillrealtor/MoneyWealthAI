"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ShieldCheck, LayoutDashboard, Users, ScrollText, LogOut, Sparkles, Landmark, Flag, Send } from "lucide-react";
import { useAdmin } from "@/lib/admin/context";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/admin", label: "Overview", icon: LayoutDashboard },
  { href: "/admin/users", label: "Users", icon: Users },
  { href: "/admin/ai", label: "AI", icon: Sparkles },
  { href: "/admin/plaid", label: "Plaid", icon: Landmark },
  { href: "/admin/flags", label: "Flags", icon: Flag },
  { href: "/admin/notifications", label: "Outbox", icon: Send },
  { href: "/admin/audit", label: "Audit", icon: ScrollText },
];

export default function ConsoleLayout({ children }: { children: React.ReactNode }) {
  const { status, role, logout } = useAdmin();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status === "unauthenticated") router.replace("/admin/login");
  }, [status, router]);

  if (status !== "authenticated") {
    return <div className="grid min-h-dvh place-items-center text-fg-subtle">Redirecting…</div>;
  }

  return (
    <div className="min-h-dvh">
      {/* distinct admin chrome: neutral, denser, iris accent */}
      <header className="sticky top-0 z-30 border-b border-line bg-ink-2/90 backdrop-blur-xl">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-5">
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-5 text-iris" />
            <span className="text-sm font-semibold tracking-tight">Fathom Admin</span>
          </div>
          <nav className="flex items-center gap-1">
            {NAV.map(({ href, label, icon: Icon }) => {
              const active = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition-colors",
                    active ? "bg-iris/15 text-iris ring-1 ring-iris/25" : "text-fg-muted hover:bg-white/5 hover:text-fg",
                  )}
                >
                  <Icon className="size-4" /> {label}
                </Link>
              );
            })}
          </nav>
          <div className="flex items-center gap-3">
            <Badge tone="neutral">{role}</Badge>
            <button onClick={logout} aria-label="Sign out" className="grid size-8 place-items-center rounded-lg text-fg-subtle hover:bg-white/5 hover:text-fg">
              <LogOut className="size-4" />
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 py-8">{children}</main>
    </div>
  );
}
