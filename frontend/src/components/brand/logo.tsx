import { cn } from "@/lib/utils";

/**
 * Fathom mark — concentric "depth soundings" (you fathom your finances) forming
 * an F-notch, in the aurora gradient. Provisional brand; swap freely once the
 * real name lands. Monogram + optional wordmark.
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
        <span className="font-display text-[1.55rem] leading-none tracking-tight text-fg">
          Fathom
        </span>
      )}
    </span>
  );
}

export function Mark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} aria-hidden>
      <defs>
        <linearGradient id="fathom-g" x1="4" y1="4" x2="28" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#19e6a0" />
          <stop offset="0.55" stopColor="#38bdf8" />
          <stop offset="1" stopColor="#7c8bff" />
        </linearGradient>
      </defs>
      {/* rounded square field */}
      <rect x="1" y="1" width="30" height="30" rx="9" fill="#0c111c" stroke="url(#fathom-g)" strokeOpacity="0.5" strokeWidth="1.2" />
      {/* concentric depth arcs */}
      <path d="M9 11.5c4.5-3 9.5-3 14 0" stroke="url(#fathom-g)" strokeWidth="2" strokeLinecap="round" />
      <path d="M11 16.5c3-2 7-2 10 0" stroke="url(#fathom-g)" strokeWidth="2" strokeLinecap="round" strokeOpacity="0.8" />
      <path d="M13.5 21.5c1.6-1 3.4-1 5 0" stroke="url(#fathom-g)" strokeWidth="2" strokeLinecap="round" strokeOpacity="0.6" />
    </svg>
  );
}
