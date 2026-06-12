/**
 * Ambient page backdrop — the signature "intelligent calm" atmosphere.
 * Fixed, pointer-events-none, pure CSS (no JS, no layout cost). Layers:
 *  1. deep ink base   2. drifting aurora blobs   3. faint grid   4. grain.
 */
export function AuroraBackdrop() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-ink"
    >
      {/* aurora blobs */}
      <div
        className="absolute -top-[20%] left-[8%] h-[55vh] w-[55vh] rounded-full opacity-50 blur-[120px] animate-[aurora_22s_ease-in-out_infinite]"
        style={{ background: "radial-gradient(circle, #19e6a0, transparent 60%)" }}
      />
      <div
        className="absolute top-[12%] right-[2%] h-[48vh] w-[48vh] rounded-full opacity-40 blur-[120px] animate-[aurora_28s_ease-in-out_infinite_reverse]"
        style={{ background: "radial-gradient(circle, #7c8bff, transparent 60%)" }}
      />
      <div
        className="absolute bottom-[-15%] left-[38%] h-[50vh] w-[50vh] rounded-full opacity-30 blur-[130px] animate-[aurora_32s_ease-in-out_infinite]"
        style={{ background: "radial-gradient(circle, #38bdf8, transparent 60%)" }}
      />

      {/* faint grid */}
      <div
        className="absolute inset-0 opacity-[0.18]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)",
          backgroundSize: "56px 56px",
          maskImage: "radial-gradient(ellipse 80% 60% at 50% 0%, #000 40%, transparent 100%)",
        }}
      />

      {/* vignette to settle the canvas */}
      <div
        className="absolute inset-0"
        style={{ background: "radial-gradient(ellipse 100% 80% at 50% -10%, transparent 50%, rgba(2,4,8,0.7))" }}
      />

      {/* grain */}
      <div
        className="absolute inset-0 opacity-[0.04] mix-blend-overlay"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
        }}
      />
    </div>
  );
}
