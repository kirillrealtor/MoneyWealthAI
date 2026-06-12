import Link from "next/link";
import {
  ArrowRight,
  Sparkles,
  ShieldCheck,
  TrendingUp,
  Target,
  Landmark,
  PiggyBank,
} from "lucide-react";
import { AdvisorDemo } from "@/components/marketing/advisor-demo";
import {
  StatsStrip,
  HowItWorks,
  FeatureGrid,
  PricingTeaser,
  FinalCTA,
} from "@/components/marketing/sections";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/ui/panel";
import { Badge, Dot } from "@/components/ui/badge";
import { Money } from "@/components/ui/money";

export default function Landing() {
  return (
    <main className="relative">
      {/* ───────────────────────── Hero ───────────────────────── */}
      <section className="mx-auto flex max-w-6xl flex-col items-center px-5 pt-40 pb-16 text-center">
        <div className="animate-[rise_0.6s_ease-out_both]">
          <Badge tone="brand" className="mb-6 py-1.5">
            <Sparkles className="size-3.5" />
            Grounded AI — never invents your numbers
          </Badge>
        </div>

        <h1 className="max-w-3xl text-balance text-5xl font-medium leading-[1.05] tracking-tight text-fg animate-[rise_0.6s_ease-out_0.05s_both] sm:text-7xl">
          Finally{" "}
          <span className="font-display italic font-normal text-aurora">understand</span>{" "}
          your money.
        </h1>

        <p className="mt-6 max-w-xl text-balance text-lg text-fg-muted animate-[rise_0.6s_ease-out_0.1s_both]">
          Fathom connects your real accounts and turns them into clear, grounded
          guidance — budgets, goals, debt and portfolio — with an AI advisor that
          shows its work.
        </p>

        <div className="mt-9 flex flex-wrap items-center justify-center gap-3 animate-[rise_0.6s_ease-out_0.15s_both]">
          <Link href="/signup">
            <Button size="lg">
              Start free <ArrowRight className="size-4" />
            </Button>
          </Link>
          <a href="#advisor">
            <Button variant="secondary" size="lg">
              See the advisor
            </Button>
          </a>
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-fg-subtle animate-[rise_0.6s_ease-out_0.2s_both]">
          <span className="inline-flex items-center gap-1.5">
            <ShieldCheck className="size-3.5 text-brand" /> 256-bit encryption
          </span>
          <span className="inline-flex items-center gap-1.5">
            <Landmark className="size-3.5 text-brand" /> Bank connections via Plaid
          </span>
          <span className="inline-flex items-center gap-1.5">
            <Dot tone="positive" /> Read-only. We never move your money.
          </span>
        </div>
      </section>

      {/* trust strip */}
      <StatsStrip />

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
        <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-white/5">
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
          <stop offset="0" stopColor="#19e6a0" stopOpacity="0.35" />
          <stop offset="1" stopColor="#19e6a0" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path
        d="M0 50 L40 44 L80 48 L120 34 L160 38 L200 24 L240 28 L280 16 L320 12"
        fill="none"
        stroke="#19e6a0"
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
      <circle cx="32" cy="32" r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="6" />
      <circle
        cx="32"
        cy="32"
        r={r}
        fill="none"
        stroke="#19e6a0"
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
