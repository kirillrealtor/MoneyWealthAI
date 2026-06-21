import { cn } from "@/lib/utils";

/**
 * MoneyWealth AI mark — concentric "wealth contours" rising in the aurora gradient,
 * suggesting growth and depth of understanding. Monogram + optional wordmark.
 */
export function Logo({
  className,
  showWordmark = true,
}: {
  className?: string;
  showWordmark?: boolean;
}) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <Mark className="h-7 w-7" />
      {showWordmark && (
        <span className="font-heading text-[1.35rem] font-semibold leading-none tracking-[-0.02em] text-fg">
          MoneyWealth<span className="text-brand"> AI</span>
        </span>
      )}
    </span>
  );
}

export function Mark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} aria-hidden>
      <defs>
        <linearGradient id="mw-g" x1="4" y1="4" x2="28" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7c3aed" />
          <stop offset="0.55" stopColor="#8b5cf6" />
          <stop offset="1" stopColor="#6366f1" />
        </linearGradient>
      </defs>
      {/* rounded square field */}
      <rect x="1" y="1" width="30" height="30" rx="9" fill="#1a1426" stroke="url(#mw-g)" strokeOpacity="0.5" strokeWidth="1.2" />
      {/* concentric depth arcs */}
      <path d="M9 11.5c4.5-3 9.5-3 14 0" stroke="url(#mw-g)" strokeWidth="2" strokeLinecap="round" />
      <path d="M11 16.5c3-2 7-2 10 0" stroke="url(#mw-g)" strokeWidth="2" strokeLinecap="round" strokeOpacity="0.8" />
      <path d="M13.5 21.5c1.6-1 3.4-1 5 0" stroke="url(#mw-g)" strokeWidth="2" strokeLinecap="round" strokeOpacity="0.6" />
    </svg>
  );
}
