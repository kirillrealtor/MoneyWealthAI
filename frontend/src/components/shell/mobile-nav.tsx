"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import * as Dialog from "@radix-ui/react-dialog";
import { Menu, X } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { NAV } from "./nav-items";
import { cn } from "@/lib/utils";

/** Mobile slide-in navigation drawer (hidden ≥ lg, where the sidebar shows). */
export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger
        aria-label="Open menu"
        className="grid size-10 place-items-center rounded-full text-fg-muted transition-colors hover:bg-white/5 hover:text-fg lg:hidden"
      >
        <Menu className="size-5" />
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm lg:hidden" />
        <Dialog.Content
          aria-label="Navigation"
          className="glass fixed inset-y-0 left-0 z-50 flex w-72 max-w-[80vw] flex-col px-4 py-5 focus:outline-none data-[state=open]:animate-[rise_0.2s_ease-out] lg:hidden"
        >
          <div className="flex items-center justify-between px-2">
            <Logo />
            <Dialog.Close aria-label="Close menu" className="grid size-9 place-items-center rounded-lg text-fg-subtle hover:bg-white/5 hover:text-fg">
              <X className="size-4" />
            </Dialog.Close>
          </div>

          <nav className="mt-7 flex flex-1 flex-col gap-1">
            {NAV.map(({ href, label, icon: Icon, enabled }) => {
              const active = pathname === href;
              if (!enabled) {
                return (
                  <span key={href} className="flex items-center justify-between rounded-[12px] px-3 py-2.5 text-sm text-fg-subtle/60">
                    <span className="flex items-center gap-3"><Icon className="size-[18px]" /> {label}</span>
                    <span className="rounded-full bg-white/5 px-1.5 py-0.5 text-[10px]">soon</span>
                  </span>
                );
              }
              return (
                <Link
                  key={href}
                  href={href}
                  onClick={() => setOpen(false)}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex items-center gap-3 rounded-[12px] px-3 py-2.5 text-sm transition-colors",
                    active ? "bg-brand/12 text-brand ring-1 ring-brand/20" : "text-fg-muted hover:bg-white/5 hover:text-fg",
                  )}
                >
                  <Icon className="size-[18px]" /> {label}
                </Link>
              );
            })}
          </nav>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
