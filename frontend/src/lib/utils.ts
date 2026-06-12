import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge conditional class names, de-duping Tailwind conflicts. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a decimal money string (as returned by the API — never a float) into a
 * locale currency string. Money arrives as a string to avoid binary-float drift.
 */
export function formatMoney(
  value: string | number,
  currency = "USD",
  opts: { compact?: boolean; signed?: boolean } = {},
) {
  const n = typeof value === "string" ? Number(value) : value;
  const fmt = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: opts.compact ? "compact" : "standard",
    maximumFractionDigits: opts.compact ? 1 : 2,
  });
  const out = fmt.format(Math.abs(n));
  if (opts.signed) return `${n < 0 ? "−" : "+"}${out}`;
  return n < 0 ? `−${out}` : out;
}
