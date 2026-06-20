/**
 * Animated hero atmosphere — pure CSS (no JS, no layout cost). Layers:
 *  1. drifting aurora blobs   2. twinkling starfield   3. rising light particles
 *  4. an occasional shooting star   5. a breathing emerald floor glow.
 * Star/particle positions are deterministic (seeded) so SSR == client (no
 * hydration mismatch). All motion respects prefers-reduced-motion globally.
 */

function seeded(a: number) {
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const r = seeded(7);
const STARS = Array.from({ length: 52 }, () => ({
  top: r() * 88,
  left: r() * 100,
  size: 1 + r() * 1.8,
  delay: r() * 6,
  dur: 2.6 + r() * 4,
}));
const PARTICLES = Array.from({ length: 16 }, () => ({
  left: r() * 100,
  delay: r() * 9,
  dur: 7 + r() * 7,
  size: 2 + r() * 2.5,
}));

export function HeroBackdrop() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* drifting aurora blobs */}
      <div
        className="absolute -left-[10%] top-[8%] h-[42vh] w-[42vh] rounded-full opacity-50 blur-[120px] animate-[aurora_24s_ease-in-out_infinite]"
        style={{ background: "radial-gradient(circle, #7c3aed, transparent 60%)" }}
      />
      <div
        className="absolute -right-[8%] top-[18%] h-[38vh] w-[38vh] rounded-full opacity-40 blur-[120px] animate-[aurora_30s_ease-in-out_infinite_reverse]"
        style={{ background: "radial-gradient(circle, #8b5cf6, transparent 60%)" }}
      />
      <div
        className="absolute bottom-[-12%] left-[32%] h-[46vh] w-[46vh] rounded-full opacity-40 blur-[130px] animate-[aurora_28s_ease-in-out_infinite]"
        style={{ background: "radial-gradient(circle, #6366f1, transparent 60%)" }}
      />

      {/* twinkling starfield */}
      {STARS.map((s, i) => (
        <span
          key={`s${i}`}
          className="absolute rounded-full bg-white"
          style={{
            top: `${s.top}%`,
            left: `${s.left}%`,
            width: s.size,
            height: s.size,
            animation: `twinkle ${s.dur}s ease-in-out ${s.delay}s infinite`,
          }}
        />
      ))}

      {/* rising light particles */}
      {PARTICLES.map((p, i) => (
        <span
          key={`p${i}`}
          className="absolute bottom-0 rounded-full"
          style={{
            left: `${p.left}%`,
            width: p.size,
            height: p.size,
            background: "rgba(167,139,250,0.9)",
            boxShadow: "0 0 8px rgba(124,58,237,0.85)",
            animation: `particle-rise ${p.dur}s linear ${p.delay}s infinite`,
          }}
        />
      ))}

      {/* shooting star */}
      <span
        className="absolute left-[14%] top-[12%] h-px w-28 bg-gradient-to-r from-white via-white/70 to-transparent"
        style={{ animation: "streak 12s ease-in 4s infinite" }}
      />

      {/* faint perspective grid, masked toward center */}
      <div
        className="absolute inset-0 opacity-[0.25]"
        style={{
          backgroundImage:
            "radial-gradient(rgba(255,255,255,0.10) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
          maskImage: "radial-gradient(ellipse 70% 55% at 50% 28%, #000 25%, transparent 78%)",
        }}
      />

      {/* breathing emerald floor glow */}
      <div
        className="absolute inset-x-0 bottom-0 h-[72%] animate-breathe"
        style={{ background: "radial-gradient(60% 90% at 50% 116%, rgba(124,58,237,0.5), transparent 72%)" }}
      />
    </div>
  );
}
