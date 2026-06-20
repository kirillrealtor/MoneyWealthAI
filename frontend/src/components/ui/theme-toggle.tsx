"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/lib/theme/context";
import { cn } from "@/lib/utils";

/**
 * Accessible light/dark switch. The sun/moon cross-fade and rotate into each
 * other. Server + first client render resolve to "light" (the store's server
 * snapshot), so hydration matches; useSyncExternalStore then reconciles to the
 * real theme and the icons animate into place — no flash, no mismatch.
 */
export function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggle } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      title={isDark ? "Light theme" : "Dark theme"}
      className={cn(
        "relative grid size-10 place-items-center rounded-full text-fg-muted outline-none transition-colors hover:bg-hover hover:text-fg focus-visible:ring-2 focus-visible:ring-brand/60 focus-visible:ring-offset-2 focus-visible:ring-offset-ink",
        className,
      )}
    >
      {/* Sun — visible in dark mode (click → light) */}
      <Sun
        className={cn(
          "absolute size-5 transition-all duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)]",
          isDark ? "rotate-0 scale-100 opacity-100" : "-rotate-90 scale-50 opacity-0",
        )}
      />
      {/* Moon — visible in light mode (click → dark) */}
      <Moon
        className={cn(
          "absolute size-5 transition-all duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)]",
          isDark ? "rotate-90 scale-50 opacity-0" : "rotate-0 scale-100 opacity-100",
        )}
      />
    </button>
  );
}
