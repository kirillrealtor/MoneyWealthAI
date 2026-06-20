"use client";

import { useState } from "react";
import Link from "next/link";
import { Bell, LogOut, ChevronDown } from "lucide-react";
import { useAuth } from "@/lib/auth/context";
import { useNotifications } from "@/lib/api/notifications";
import { Badge } from "@/components/ui/badge";
import { Mark } from "@/components/brand/logo";
import { MobileNav } from "./mobile-nav";

export function Topbar() {
  const { user, logout } = useAuth();
  const { data: notif } = useNotifications();
  const [menu, setMenu] = useState(false);
  const initial = (user?.full_name || user?.email || "?").charAt(0).toUpperCase();
  const unread = notif?.unread_count ?? 0;

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-3 border-b border-line bg-ink/70 px-4 backdrop-blur-xl sm:px-6">
      {/* mobile: menu + brand */}
      <div className="flex items-center gap-1 lg:hidden">
        <MobileNav />
        <Mark className="size-7" />
      </div>

      <div className="flex flex-1 items-center" />

      <div className="flex items-center gap-2">
        <Link
          href="/app/notifications"
          aria-label={unread > 0 ? `Notifications, ${unread} unread` : "Notifications"}
          className="relative grid size-10 place-items-center rounded-full text-fg-muted transition-colors hover:bg-black/5 hover:text-fg"
        >
          <Bell className="size-5" />
          {unread > 0 && (
            <span className="absolute right-1.5 top-1.5 grid min-h-[16px] min-w-[16px] place-items-center rounded-full bg-brand px-1 text-[10px] font-semibold text-ink">
              {unread > 9 ? "9+" : unread}
            </span>
          )}
        </Link>

        <div className="relative">
          <button
            onClick={() => setMenu((m) => !m)}
            className="flex items-center gap-2 rounded-full py-1 pl-1 pr-2.5 transition-colors hover:bg-black/5"
            aria-haspopup="menu"
            aria-expanded={menu}
          >
            <span className="grid size-8 place-items-center rounded-full bg-brand/15 text-sm font-medium text-brand ring-1 ring-brand/25">
              {initial}
            </span>
            <ChevronDown className="size-4 text-fg-subtle" />
          </button>

          {menu && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setMenu(false)} />
              <div
                role="menu"
                className="glass absolute right-0 z-20 mt-2 w-60 rounded-[14px] p-2"
              >
                <div className="px-3 py-2">
                  <p className="truncate text-sm font-medium text-fg">
                    {user?.full_name || user?.email}
                  </p>
                  <div className="mt-1.5">
                    <Badge tone={user?.tier === "free" ? "neutral" : "brand"}>
                      {user?.tier ?? "free"} plan
                    </Badge>
                  </div>
                </div>
                <div className="my-1 h-px bg-line" />
                <button
                  role="menuitem"
                  onClick={() => logout()}
                  className="flex w-full items-center gap-2.5 rounded-[10px] px-3 py-2 text-sm text-fg-muted transition-colors hover:bg-black/5 hover:text-fg"
                >
                  <LogOut className="size-4" /> Log out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
