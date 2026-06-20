"use client";

import { useCallback, useSyncExternalStore } from "react";
import { THEME_STORAGE_KEY } from "./script";

export type Theme = "light" | "dark";

/**
 * Theme store backed by the DOM — the `.dark` class on <html> *is* the source
 * of truth (set pre-paint by the blocking script in layout.tsx). We read it via
 * useSyncExternalStore, which is the React-blessed way to subscribe to external
 * state: no setState-in-effect, no cascading renders, and hydration-safe (server
 * + first client render use the server snapshot, then React reconciles).
 */

const listeners = new Set<() => void>();
function emit() {
  for (const l of listeners) l();
}

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
  root.style.colorScheme = theme;
}

function subscribe(onChange: () => void) {
  listeners.add(onChange);
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  const onSystemChange = () => {
    // Only follow the OS while the user hasn't pinned an explicit choice.
    try {
      if (localStorage.getItem(THEME_STORAGE_KEY)) return;
    } catch {
      /* ignore */
    }
    applyTheme(mq.matches ? "dark" : "light");
    emit();
  };
  mq.addEventListener("change", onSystemChange);
  return () => {
    listeners.delete(onChange);
    mq.removeEventListener("change", onSystemChange);
  };
}

function getSnapshot(): Theme {
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

function getServerSnapshot(): Theme {
  return "light";
}

/** Set and persist the theme; notifies every subscribed component. */
export function setTheme(theme: Theme) {
  applyTheme(theme);
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    /* storage may be unavailable (private mode) — theme still applies this session */
  }
  emit();
}

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const toggle = useCallback(() => {
    setTheme(getSnapshot() === "dark" ? "light" : "dark");
  }, []);
  return { theme, setTheme, toggle };
}
