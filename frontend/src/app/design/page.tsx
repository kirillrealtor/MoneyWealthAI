import type { CSSProperties, ReactNode } from "react";
import { Sparkles, TrendingUp, Wallet, Target, ArrowUpRight, Send } from "lucide-react";

/**
 * /design — three visual directions for the product, each a different color
 * combination on a light canvas, rendered as a realistic mini-dashboard so the
 * look can be judged in context. This is a standalone showcase page (no auth,
 * no app shell); it doesn't touch the live app's theme.
 */

type Palette = {
  key: string;
  name: string;
  vibe: string;
  font: string;
  bg: string;
  surface: string;
  surface2: string;
  border: string;
  text: string;
  muted: string;
  subtle: string;
  brand: string;
  brandSoft: string;
  onBrand: string;
  accent: string;
  positive: string;
  negative: string;
  shadow: string;
};

const DIRECTIONS: Palette[] = [
  {
    key: "indigo",
    name: "Indigo Clarity",
    vibe: "Crisp, trustworthy SaaS — white canvas, confident indigo, cool slate.",
    font: "var(--font-sans)",
    bg: "#FFFFFF",
    surface: "#FFFFFF",
    surface2: "#F6F7FB",
    border: "#E7E9F1",
    text: "#0F1222",
    muted: "#5B6178",
    subtle: "#8A90A6",
    brand: "#4F46E5",
    brandSoft: "#EEF0FE",
    onBrand: "#FFFFFF",
    accent: "#0EA5E9",
    positive: "#0E9F6E",
    negative: "#E02424",
    shadow: "0 1px 2px rgba(16,18,34,.05), 0 10px 30px rgba(16,18,34,.07)",
  },
  {
    key: "emerald",
    name: "Emerald Calm",
    vibe: "Warm, reassuring money-app — mint-tinted white, emerald, soft sage.",
    font: "var(--font-sans)",
    bg: "#F6FBF8",
    surface: "#FFFFFF",
    surface2: "#F1F8F4",
    border: "#DEEBE4",
    text: "#0B1B14",
    muted: "#4E6157",
    subtle: "#84978B",
    brand: "#0E9F6E",
    brandSoft: "#E6F6EE",
    onBrand: "#FFFFFF",
    accent: "#0E9AA5",
    positive: "#0E9F6E",
    negative: "#C2410C",
    shadow: "0 1px 2px rgba(11,27,20,.05), 0 10px 30px rgba(11,27,20,.06)",
  },
  {
    key: "violet",
    name: "Violet Premium",
    vibe: "Modern, premium — porcelain off-white, violet, amber highlights.",
    font: "var(--font-sans)",
    bg: "#FCFBFE",
    surface: "#FFFFFF",
    surface2: "#F7F4FC",
    border: "#ECE6F4",
    text: "#1A1426",
    muted: "#655B73",
    subtle: "#9890A4",
    brand: "#7C3AED",
    brandSoft: "#F3EEFE",
    onBrand: "#FFFFFF",
    accent: "#F59E0B",
    positive: "#16A34A",
    negative: "#DC2626",
    shadow: "0 1px 2px rgba(26,20,38,.05), 0 10px 30px rgba(26,20,38,.07)",
  },
];

export default function DesignDirectionsPage() {
  return (
    <main style={{ background: "#0b0e16", minHeight: "100dvh", padding: "48px 20px" }}>
      <div style={{ maxWidth: 980, margin: "0 auto" }}>
        <header style={{ marginBottom: 36, color: "#e8eef4" }}>
          <p style={{ fontSize: 13, letterSpacing: "0.18em", textTransform: "uppercase", color: "#7c8bff" }}>
            MoneyWealth AI · design directions
          </p>
          <h1 style={{ fontSize: 34, fontWeight: 600, letterSpacing: "-0.02em", marginTop: 10 }}>
            Three directions. Pick one.
          </h1>
          <p style={{ color: "#9db0c2", marginTop: 8, maxWidth: 620, lineHeight: 1.6 }}>
            Each is a different color combination on a light canvas, shown as a real dashboard so you can
            judge it in context. Tell me the name you like and I&apos;ll roll it across the whole app.
          </p>
        </header>

        <div style={{ display: "flex", flexDirection: "column", gap: 40 }}>
          {DIRECTIONS.map((p) => (
            <section key={p.key}>
              <DirectionLabel p={p} />
              <Preview p={p} />
            </section>
          ))}
        </div>
      </div>
    </main>
  );
}

function DirectionLabel({ p }: { p: Palette }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12, gap: 16 }}>
      <div>
        <h2 style={{ color: "#e8eef4", fontSize: 20, fontWeight: 600 }}>{p.name}</h2>
        <p style={{ color: "#9db0c2", fontSize: 13.5, marginTop: 2 }}>{p.vibe}</p>
      </div>
      <div style={{ display: "flex", gap: 6 }}>
        {[p.bg, p.brand, p.accent, p.positive, p.text].map((c, i) => (
          <span
            key={i}
            title={c}
            style={{ width: 22, height: 22, borderRadius: 6, background: c, border: "1px solid rgba(255,255,255,.15)" }}
          />
        ))}
      </div>
    </div>
  );
}

function Preview({ p }: { p: Palette }) {
  const card: CSSProperties = {
    background: p.surface,
    border: `1px solid ${p.border}`,
    borderRadius: 16,
    padding: 18,
    boxShadow: p.shadow,
  };

  return (
    <div
      style={{
        background: p.bg,
        border: `1px solid ${p.border}`,
        borderRadius: 20,
        overflow: "hidden",
        boxShadow: "0 24px 60px rgba(0,0,0,.4)",
        fontFamily: p.font,
        color: p.text,
      }}
    >
      {/* browser chrome */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "12px 16px", background: p.surface2, borderBottom: `1px solid ${p.border}` }}>
        <span style={{ width: 11, height: 11, borderRadius: 99, background: "#ff5f57" }} />
        <span style={{ width: 11, height: 11, borderRadius: 99, background: "#febc2e" }} />
        <span style={{ width: 11, height: 11, borderRadius: 99, background: "#28c840" }} />
        <span style={{ marginLeft: 12, fontSize: 12, color: p.subtle }}>moneywealth.ai / dashboard</span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "200px 1fr", minHeight: 440 }}>
        {/* sidebar */}
        <aside style={{ borderRight: `1px solid ${p.border}`, padding: 18, background: p.surface }}>
          <Brand p={p} />
          <nav style={{ marginTop: 22, display: "flex", flexDirection: "column", gap: 2 }}>
            {[
              { label: "Dashboard", active: true, icon: TrendingUp },
              { label: "Budgets", icon: Wallet },
              { label: "Goals", icon: Target },
              { label: "Advisor", icon: Sparkles },
            ].map((n) => (
              <div
                key={n.label}
                style={{
                  display: "flex", alignItems: "center", gap: 10, padding: "9px 11px", borderRadius: 10,
                  fontSize: 14,
                  background: n.active ? p.brandSoft : "transparent",
                  color: n.active ? p.brand : p.muted,
                  fontWeight: n.active ? 600 : 500,
                }}
              >
                <n.icon size={17} /> {n.label}
              </div>
            ))}
          </nav>
        </aside>

        {/* content */}
        <div style={{ padding: 22, background: p.bg }}>
          <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 18 }}>
            <div>
              <p style={{ fontSize: 13, color: p.subtle }}>Good morning,</p>
              <h3 style={{ fontSize: 26, fontWeight: 600, letterSpacing: "-0.02em" }}>Hassan.</h3>
            </div>
            <button
              style={{
                display: "inline-flex", alignItems: "center", gap: 7, padding: "9px 14px", borderRadius: 11,
                background: p.brand, color: p.onBrand, border: "none", fontSize: 13.5, fontWeight: 600, cursor: "pointer",
                boxShadow: p.shadow,
              }}
            >
              <Sparkles size={15} /> Ask your advisor
            </button>
          </div>

          {/* stat cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
            <div style={card}>
              <Row p={p} label="Net worth" icon={<TrendingUp size={16} color={p.subtle} />} />
              <p style={{ fontSize: 24, fontWeight: 600, letterSpacing: "-0.02em", fontVariantNumeric: "tabular-nums" }}>$48,250</p>
              <p style={{ fontSize: 12, color: p.positive, display: "flex", alignItems: "center", gap: 3, marginTop: 2 }}>
                <ArrowUpRight size={13} /> +2.4% this month
              </p>
            </div>
            <div style={card}>
              <Row p={p} label="Budgets" icon={<Wallet size={16} color={p.brand} />} />
              <p style={{ fontSize: 24, fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>
                $1,240 <span style={{ fontSize: 15, color: p.subtle }}>/ $2,000</span>
              </p>
              <Bar p={p} pct={62} color={p.brand} />
            </div>
            <div style={card}>
              <Row p={p} label="Goals" icon={<Target size={16} color={p.accent} />} />
              <p style={{ fontSize: 24, fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>64%</p>
              <Bar p={p} pct={64} color={p.accent} />
            </div>
          </div>

          {/* advisor bubble */}
          <div style={{ ...card, marginTop: 14, display: "flex", gap: 12, alignItems: "flex-start", background: p.surface2 }}>
            <span style={{ width: 30, height: 30, borderRadius: 99, background: p.brand, display: "grid", placeItems: "center", flexShrink: 0 }}>
              <Sparkles size={15} color={p.onBrand} />
            </span>
            <div style={{ fontSize: 14, lineHeight: 1.55, color: p.text }}>
              You&apos;re <b style={{ color: p.positive }}>$760 under budget</b> this month — nice work. Want me to move the
              surplus toward your <b style={{ color: p.brand }}>car goal</b>? You&apos;d hit it 2 months sooner.
            </div>
          </div>

          {/* composer + spending bars */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 150px", gap: 12, marginTop: 14, alignItems: "stretch" }}>
            <div style={{ ...card, display: "flex", alignItems: "center", justifyContent: "space-between", padding: 12 }}>
              <span style={{ fontSize: 13.5, color: p.subtle }}>Ask about your budgets, goals, debt…</span>
              <span style={{ width: 32, height: 32, borderRadius: 9, background: p.brand, display: "grid", placeItems: "center" }}>
                <Send size={15} color={p.onBrand} />
              </span>
            </div>
            <div style={{ ...card, padding: 12, display: "flex", alignItems: "flex-end", gap: 5, height: 64 }}>
              {[40, 70, 35, 90, 55, 75].map((h, i) => (
                <span key={i} style={{ flex: 1, height: `${h}%`, background: i === 3 ? p.accent : p.brandSoft, borderRadius: 3 }} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Brand({ p }: { p: Palette }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
      <span
        style={{
          width: 28, height: 28, borderRadius: 9, display: "grid", placeItems: "center",
          background: `linear-gradient(135deg, ${p.brand}, ${p.accent})`, color: "#fff", fontWeight: 700, fontSize: 15,
        }}
      >
        M
      </span>
      <span style={{ fontWeight: 600, fontSize: 15, letterSpacing: "-0.01em" }}>MoneyWealth</span>
    </div>
  );
}

function Row({ p, label, icon }: { p: Palette; label: string; icon: ReactNode }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
      <span style={{ fontSize: 12.5, color: p.muted, fontWeight: 500 }}>{label}</span>
      {icon}
    </div>
  );
}

function Bar({ p, pct, color }: { p: Palette; pct: number; color: string }) {
  return (
    <div style={{ height: 7, background: p.surface2, borderRadius: 99, overflow: "hidden", marginTop: 10, border: `1px solid ${p.border}` }}>
      <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 99 }} />
    </div>
  );
}
