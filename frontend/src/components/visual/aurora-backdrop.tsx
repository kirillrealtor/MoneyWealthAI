/**
 * Ambient page backdrop — the signature "intelligent calm" atmosphere.
 * Fixed, pointer-events-none, pure CSS (no JS, no layout cost). Fully
 * theme-aware: every color reads a CSS variable that flips under `.dark`
 * (see globals.css), so the same component reads right on white and on near-black.
 * Layers:  1. canvas base   2. drifting aurora blobs   3. faint grid   4. wash.
 */
export function AuroraBackdrop() {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-ink"
    >
      {/* aurora blobs — emerald/teal read well on both themes; opacity flips */}
      <div
        className="absolute -top-[20%] left-[8%] h-[55vh] w-[55vh] rounded-full blur-[90px] will-change-transform animate-[aurora_22s_ease-in-out_infinite]"
        style={{
          background: "radial-gradient(circle, var(--color-brand), transparent 60%)",
          opacity: "var(--aurora-blob)",
        }}
      />
      <div
        className="absolute top-[12%] right-[2%] h-[48vh] w-[48vh] rounded-full blur-[90px] will-change-transform animate-[aurora_28s_ease-in-out_infinite_reverse]"
        style={{
          background: "radial-gradient(circle, var(--color-iris), transparent 60%)",
          opacity: "calc(var(--aurora-blob) + 0.05)",
        }}
      />
      <div
        className="absolute bottom-[-15%] left-[38%] h-[50vh] w-[50vh] rounded-full blur-[90px] will-change-transform animate-[aurora_32s_ease-in-out_infinite]"
        style={{
          background: "radial-gradient(circle, var(--color-sky), transparent 60%)",
          opacity: "var(--aurora-blob)",
        }}
      />

      {/* faint grid — dark hairlines on light, light hairlines on dark */}
      <div
        className="absolute inset-0 opacity-50"
        style={{
          backgroundImage:
            "linear-gradient(var(--aurora-grid) 1px, transparent 1px), linear-gradient(90deg, var(--aurora-grid) 1px, transparent 1px)",
          backgroundSize: "56px 56px",
          maskImage: "radial-gradient(ellipse 80% 60% at 50% 0%, #000 40%, transparent 100%)",
        }}
      />

      {/* soft top wash to lift the canvas */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 90% 55% at 50% -10%, var(--aurora-wash), transparent 60%)",
        }}
      />
    </div>
  );
}
