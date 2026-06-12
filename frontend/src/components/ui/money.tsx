import { cn } from "@/lib/utils";
import { formatMoney } from "@/lib/utils";

/**
 * Money — tabular, sign-semantic (emerald up / coral down), screen-reader safe.
 * Money arrives from the API as a decimal string; never a float.
 */
export function Money({
  value,
  currency = "USD",
  signed = false,
  compact = false,
  colorize = false,
  className,
}: {
  value: string | number;
  currency?: string;
  signed?: boolean;
  compact?: boolean;
  colorize?: boolean;
  className?: string;
}) {
  const n = typeof value === "string" ? Number(value) : value;
  const text = formatMoney(value, currency, { compact, signed });
  return (
    <span
      className={cn(
        "tnum",
        colorize && (n < 0 ? "text-negative" : n > 0 ? "text-positive" : "text-fg-muted"),
        className,
      )}
    >
      <span aria-hidden>{text}</span>
      <span className="sr-only">
        {n < 0 ? "negative " : ""}
        {formatMoney(Math.abs(n), currency)}
      </span>
    </span>
  );
}
