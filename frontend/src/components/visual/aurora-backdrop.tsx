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
        className="absolute -top-[20%] left-[8%] h-[55vh] w-[55vh] rounded-full opacity-20 blur-[140px] animate-[aurora_22s_ease-in-out_infinite]"
        style={{ background: "radial-gradient(circle, #0e9f6e, transparent 60%)" }}
      />
      <div
        className="absolute top-[12%] right-[2%] h-[48vh] w-[48vh] rounded-full opacity-25 blur-[130px] animate-[aurora_28s_ease-in-out_infinite_reverse]"
        style={{ background: "radial-gradient(circle, #0e9aa5, transparent 60%)" }}
      />
      <div
        className="absolute bottom-[-15%] left-[38%] h-[50vh] w-[50vh] rounded-full opacity-20 blur-[140px] animate-[aurora_32s_ease-in-out_infinite]"
        style={{ background: "radial-gradient(circle, #14b8a6, transparent 60%)" }}
      />

      {/* faint grid (subtle dark lines on the light canvas) */}
      <div
        className="absolute inset-0 opacity-50"
        style={{
          backgroundImage:
            "linear-gradient(rgba(11,27,20,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(11,27,20,0.035) 1px, transparent 1px)",
          backgroundSize: "56px 56px",
          maskImage: "radial-gradient(ellipse 80% 60% at 50% 0%, #000 40%, transparent 100%)",
        }}
      />

      {/* soft top wash to lift the canvas (light, never darkens) */}
      <div
        className="absolute inset-0"
        style={{ background: "radial-gradient(ellipse 90% 55% at 50% -10%, rgba(255,255,255,0.6), transparent 60%)" }}
      />
    </div>
  );
}
