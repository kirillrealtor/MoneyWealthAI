import Link from "next/link";
import {
  ArrowRight,
  Sparkles,
  TrendingUp,
  Target,
  PiggyBank,
  LayoutDashboard,
  Wallet,
  PieChart,
} from "lucide-react";
import { AdvisorDemo } from "@/components/marketing/advisor-demo";
import {
  HowItWorks,
  FeatureGrid,
  PricingTeaser,
  FinalCTA,
} from "@/components/marketing/sections";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/ui/panel";
import { Badge } from "@/components/ui/badge";
import { Money } from "@/components/ui/money";
import { cn } from "@/lib/utils";

export default function Landing() {
  return (
    <main className="relative">
      <Hero />
      <ProductShowcase />

      {/* ───────────────── Advisor showcase (live stream) ───────────────── */}
      <section id="advisor" className="mx-auto max-w-6xl px-5 pt-24 pb-8">
        <AdvisorShowcase />
      </section>

      {/* ───────────────── Bento product preview ───────────────── */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <div className="mb-10 text-center">
          <span className="text-xs font-medium uppercase tracking-[0.2em] text-brand">
            Your money, at a glance
          </span>
          <h2 className="mt-3 text-3xl font-medium tracking-tight sm:text-4xl">
            Not a dashboard dump — each surface answers a{" "}
            <span className="font-display italic text-aurora">real</span> question.
          </h2>
        </div>
        <BentoGrid />
      </section>

      <HowItWorks />
      <FeatureGrid />
      <PricingTeaser />
      <FinalCTA />
    </main>
  );
}

/* ================================== Hero ================================== */
function Hero() {
  return (
    <section className="relative isolate overflow-hidden bg-[#06120c] text-white">
      {/* emerald glow rising from the bottom + a teal halo up top */}
      <div
        className="pointer-events-none absolute inset-x-0 bottom-0 h-[70%]"
        style={{ background: "radial-gradient(60% 90% at 50% 115%, rgba(14,159,110,0.55), transparent 72%)" }}
      />
      <div
        className="pointer-events-none absolute left-1/2 top-[-12rem] h-[34rem] w-[64rem] -translate-x-1/2 rounded-full opacity-40 blur-[140px]"
        style={{ background: "radial-gradient(circle, rgba(20,184,166,0.45), transparent 62%)" }}
      />
      {/* faint star grid */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage:
            "radial-gradient(rgba(255,255,255,0.10) 1px, transparent 1px)",
          backgroundSize: "26px 26px",
          maskImage: "radial-gradient(ellipse 70% 60% at 50% 30%, #000 30%, transparent 80%)",
        }}
      />

      <div className="relative mx-auto max-w-6xl px-5 pt-40 text-center">
        <h1 className="mx-auto max-w-4xl text-balance text-5xl font-semibold leading-[1.02] tracking-tight animate-[rise_0.6s_ease-out_0.05s_both] sm:text-7xl">
          <span className="font-display text-[0.92em] font-normal italic text-white/55">Finally</span>{" "}
          <span className="bg-gradient-to-b from-white to-zinc-400 bg-clip-text text-transparent">understand</span>
          <br />
          <span className="bg-gradient-to-b from-white to-zinc-400 bg-clip-text text-transparent">your</span>{" "}
          <span className="font-display font-normal italic text-white/55">money.</span>
        </h1>

        <p className="mx-auto mt-7 max-w-xl text-balance text-lg text-white/60 animate-[rise_0.6s_ease-out_0.1s_both]">
          MoneyWealth AI turns your real accounts into clear, grounded guidance — an AI
          advisor that shows its work and never invents your numbers.
        </p>

        <div className="mt-9 flex flex-wrap items-center justify-center gap-3 animate-[rise_0.6s_ease-out_0.15s_both]">
          <Link href="/signup">
            <Button size="lg">
              Start free <ArrowRight className="size-4" />
            </Button>
          </Link>
          <a
            href="#advisor"
            className="inline-flex h-12 items-center gap-2 rounded-[12px] border border-white/20 bg-white/5 px-6 text-[0.95rem] font-medium text-white backdrop-blur transition-colors hover:bg-white/10"
          >
            See the advisor
          </a>
        </div>

        <ProductCards />
      </div>
    </section>
  );
}

const PRODUCTS = [
  { name: "Dashboard", icon: LayoutDashboard, blurb: "Your whole picture" },
  { name: "Budgets", icon: Wallet, blurb: "Pace, live" },
  { name: "Advisor", icon: Sparkles, blurb: "Ask anything", featured: true },
  { name: "Goals", icon: Target, blurb: "Reverse-engineered" },
  { name: "Portfolio", icon: PieChart, blurb: "Allocation & drift" },
];

function ProductCards() {
  return (
    <div className="mt-16 flex items-end justify-center gap-3 overflow-x-auto px-1 pb-px sm:overflow-visible">
      {PRODUCTS.map((p, i) => (
        <div
          key={p.name}
          className={cn(
            "relative shrink-0 rounded-2xl border p-4 text-left backdrop-blur transition-all",
            "animate-[rise_0.6s_ease-out_both]",
            p.featured
              ? "-translate-y-5 border-brand/50 bg-[#08231a] shadow-[0_0_70px_-12px_rgba(14,159,110,0.75)]"
              : "border-white/10 bg-white/[0.04] hover:border-white/20",
          )}
          style={{ width: p.featured ? 188 : 150, animationDelay: `${0.2 + i * 0.05}s` }}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-white">{p.name}</span>
            <p.icon className={cn("size-4", p.featured ? "text-brand" : "text-white/50")} />
          </div>
          <div
            className={cn(
              "mt-3 grid h-20 place-items-center rounded-lg",
              p.featured
                ? "bg-gradient-to-br from-brand/30 to-iris/20 ring-1 ring-brand/30"
                : "bg-white/[0.04] ring-1 ring-white/5",
            )}
          >
            <p.icon className={cn(p.featured ? "size-7 text-brand" : "size-6 text-white/30")} />
          </div>
          <p className="mt-2.5 text-xs text-white/50">{p.blurb}</p>
        </div>
      ))}
    </div>
  );
}

/* =========================== Transition headline =========================== */
function ProductShowcase() {
  return (
    <section className="relative mx-auto max-w-4xl px-5 pt-20 pb-4 text-center">
      <Badge tone="brand" className="mb-6">
        <Sparkles className="size-3.5" /> One calm app
      </Badge>
      <h2 className="text-balance text-4xl font-semibold tracking-tight text-fg sm:text-5xl">
        Where your money finally{" "}
        <span className="font-display italic font-normal text-aurora">makes sense.</span>
      </h2>
      <p className="mx-auto mt-4 max-w-xl text-fg-muted">
        Every surface answers a real question — and the advisor ties them together.
      </p>
    </section>
  );
}

/* ============================ Advisor showcase ============================ */
function AdvisorShowcase() {
  return (
    <Panel className="overflow-hidden p-0 animate-[rise_0.7s_ease-out_both]">
      <div className="grid gap-0 md:grid-cols-[1.1fr_1fr]">
        {/* Left: pitch */}
        <div className="flex flex-col justify-center gap-5 p-8 sm:p-10">
          <Badge tone="brand" className="w-fit">
            <Sparkles className="size-3.5" /> The advisor
          </Badge>
          <h3 className="text-2xl font-medium leading-snug tracking-tight sm:text-3xl">
            Ask anything. Get answers{" "}
            <span className="font-display italic text-aurora">tied to your data.</span>
          </h3>
          <p className="text-fg-muted">
            Every figure is traceable. The advisor calls your real accounts,
            cites what it used, and tells you honestly when it doesn&apos;t know —
            no hallucinated balances, no generic platitudes.
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge>Grounded</Badge>
            <Badge>Cites its sources</Badge>
            <Badge>Streams in real time</Badge>
          </div>
        </div>

        {/* Right: live streaming conversation */}
        <div className="relative border-t border-line bg-ink/40 p-6 sm:p-8 md:border-l md:border-t-0">
          <AdvisorDemo />
        </div>
      </div>
    </Panel>
  );
}

/* ============================== Bento grid ============================== */
function BentoGrid() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {/* Net worth — wide */}
      <Panel interactive className="sm:col-span-2 animate-[rise_0.6s_ease-out_both]">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-fg-subtle">Net worth</p>
            <p className="mt-1 text-4xl font-medium tracking-tight tnum">
              <Money value="48215.90" />
            </p>
            <p className="mt-1 inline-flex items-center gap-1 text-sm text-positive">
              <TrendingUp className="size-4" /> <Money value="1240.18" signed /> this month
            </p>
          </div>
          <Badge tone="positive">+2.6%</Badge>
        </div>
        <Sparkline />
      </Panel>

      {/* Advisor mini */}
      <Panel interactive className="relative overflow-hidden animate-[rise_0.6s_ease-out_0.05s_both]">
        <div className="absolute -right-6 -top-6 size-24 rounded-full bg-brand/20 blur-2xl" />
        <Sparkles className="size-5 text-brand" />
        <p className="mt-3 text-sm font-medium">Advisor nudge</p>
        <p className="mt-1 text-sm text-fg-muted">
          &ldquo;Move <span className="text-fg">$200</span> to your Emergency Fund to stay on
          pace for August.&rdquo;
        </p>
      </Panel>

      {/* Budget ring */}
      <Panel interactive className="animate-[rise_0.6s_ease-out_0.1s_both]">
        <div className="flex items-center gap-4">
          <Ring pct={69} />
          <div>
            <p className="text-sm font-medium">Dining</p>
            <p className="text-xs text-fg-subtle">
              <Money value="312.40" /> / <Money value="450" />
            </p>
            <Badge tone="positive" className="mt-2">On track</Badge>
          </div>
        </div>
      </Panel>

      {/* Goal */}
      <Panel interactive className="animate-[rise_0.6s_ease-out_0.15s_both]">
        <Target className="size-5 text-iris" />
        <p className="mt-3 text-sm font-medium">Emergency Fund</p>
        <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-black/5">
          <div className="h-full rounded-full bg-gradient-to-r from-brand to-sky" style={{ width: "52%" }} />
        </div>
        <p className="mt-2 text-xs text-fg-subtle">
          <Money value="5200" /> of <Money value="10000" /> · <Money value="833" />/mo
        </p>
      </Panel>

      {/* Debt */}
      <Panel interactive className="animate-[rise_0.6s_ease-out_0.2s_both]">
        <PiggyBank className="size-5 text-warning" />
        <p className="mt-3 text-sm font-medium">Debt-free in</p>
        <p className="mt-1 text-2xl font-medium tracking-tight">2y 4m</p>
        <p className="mt-1 text-xs text-fg-subtle">Avalanche · saves <Money value="1180" /> interest</p>
      </Panel>
    </div>
  );
}

function Sparkline() {
  return (
    <svg viewBox="0 0 320 64" className="mt-4 w-full" preserveAspectRatio="none" aria-hidden>
      <defs>
        <linearGradient id="spark" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#0e9f6e" stopOpacity="0.35" />
          <stop offset="1" stopColor="#0e9f6e" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path
        d="M0 50 L40 44 L80 48 L120 34 L160 38 L200 24 L240 28 L280 16 L320 12"
        fill="none"
        stroke="#0e9f6e"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M0 50 L40 44 L80 48 L120 34 L160 38 L200 24 L240 28 L280 16 L320 12 L320 64 L0 64 Z"
        fill="url(#spark)"
      />
    </svg>
  );
}

function Ring({ pct }: { pct: number }) {
  const r = 26;
  const c = 2 * Math.PI * r;
  return (
    <svg viewBox="0 0 64 64" className="size-16 -rotate-90" aria-hidden>
      <circle cx="32" cy="32" r={r} fill="none" stroke="rgba(11,27,20,0.08)" strokeWidth="6" />
      <circle
        cx="32"
        cy="32"
        r={r}
        fill="none"
        stroke="#0e9f6e"
        strokeWidth="6"
        strokeLinecap="round"
        strokeDasharray={c}
        strokeDashoffset={c * (1 - pct / 100)}
      />
      <text
        x="32"
        y="33"
        transform="rotate(90 32 32)"
        textAnchor="middle"
        dominantBaseline="middle"
        className="fill-fg text-[13px] font-medium tnum"
      >
        {pct}%
      </text>
    </svg>
  );
}
