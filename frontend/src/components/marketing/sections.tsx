import Link from "next/link";
import {
  Sparkles,
  Wallet,
  Target,
  TrendingDown,
  PieChart,
  BellRing,
  Link2,
  Brain,
  Compass,
  Check,
  ShieldCheck,
  Landmark,
  Lock,
} from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

/* ─────────────────────────── Trust / stats strip ─────────────────────────── */
export function StatsStrip() {
  const items = [
    { icon: Landmark, label: "12,000+ banks", sub: "connected via Plaid" },
    { icon: Lock, label: "256-bit AES", sub: "encrypted at rest" },
    { icon: Sparkles, label: "Grounded", sub: "every figure cited" },
    { icon: ShieldCheck, label: "Read-only", sub: "we never move money" },
  ];
  return (
    <div className="mx-auto max-w-5xl px-5">
      <Panel className="grid grid-cols-2 gap-px overflow-hidden p-0 md:grid-cols-4">
        {items.map(({ icon: Icon, label, sub }) => (
          <div key={label} className="flex items-center gap-3 px-5 py-4">
            <Icon className="size-5 shrink-0 text-brand" />
            <div>
              <p className="text-sm font-medium text-fg">{label}</p>
              <p className="text-xs text-fg-subtle">{sub}</p>
            </div>
          </div>
        ))}
      </Panel>
    </div>
  );
}

/* ────────────────────────────── How it works ────────────────────────────── */
export function HowItWorks() {
  const steps = [
    { icon: Link2, title: "Connect securely", body: "Link your banks through Plaid in seconds. Tokens are encrypted; access is read-only." },
    { icon: Brain, title: "MoneyWealth AI understands", body: "The advisor reads your real transactions, budgets, debt and holdings — grounded, never guessed." },
    { icon: Compass, title: "Act with clarity", body: "Get one clear next step at a time — what to pay, save, or move, and exactly why." },
  ];
  return (
    <section className="mx-auto max-w-6xl px-5 py-24">
      <Heading kicker="How it works" title="From bank login to" em="clarity" rest="in three steps." />
      <div className="mt-12 grid gap-4 md:grid-cols-3">
        {steps.map(({ icon: Icon, title, body }, i) => (
          <Panel key={title} className="relative">
            <span className="font-display text-5xl italic text-aurora">{i + 1}</span>
            <Icon className="mt-4 size-6 text-brand" />
            <h3 className="mt-3 text-lg font-medium">{title}</h3>
            <p className="mt-1.5 text-sm text-fg-muted">{body}</p>
          </Panel>
        ))}
      </div>
    </section>
  );
}

/* ─────────────────────────────── Feature grid ────────────────────────────── */
export function FeatureGrid() {
  const features = [
    { icon: Sparkles, title: "AI Advisor", body: "Ask anything about your money. Grounded answers that cite the data they used.", tone: "brand" as const },
    { icon: Wallet, title: "Budgets", body: "Per-category limits with live pacing — know if you're on track before month-end." },
    { icon: Target, title: "Goals", body: "Set a target and date; we reverse-engineer the monthly amount and track it." },
    { icon: TrendingDown, title: "Debt payoff", body: "Snowball vs. avalanche, side by side — see your debt-free date and interest saved." },
    { icon: PieChart, title: "Portfolio", body: "Allocation, drift and concentration at a glance. Informational, never a trade nudge." },
    { icon: BellRing, title: "Proactive alerts", body: "Overspend, unusual charges and goal milestones — quietly, respecting your quiet hours." },
  ];
  return (
    <section id="features" className="mx-auto max-w-6xl px-5 py-24">
      <Heading kicker="Everything in one place" title="A whole financial team," em="one" rest="calm app." />
      <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map(({ icon: Icon, title, body, tone }) => (
          <Panel key={title} interactive className="group">
            <div className="flex size-11 items-center justify-center rounded-xl bg-hover ring-1 ring-line transition-colors group-hover:ring-brand/40">
              <Icon className={tone === "brand" ? "size-5 text-brand" : "size-5 text-fg-muted"} />
            </div>
            <h3 className="mt-4 text-base font-medium">{title}</h3>
            <p className="mt-1.5 text-sm text-fg-muted">{body}</p>
          </Panel>
        ))}
      </div>
    </section>
  );
}

/* ──────────────────────────────── Pricing ───────────────────────────────── */
export function PricingTeaser() {
  const plans = [
    { name: "Free", price: "$0", note: "Get started", features: ["All dashboards", "Budgets & goals", "100 advisor messages/mo"], cta: "Start free", highlight: false },
    { name: "Plus", price: "$12", note: "per month", features: ["Everything in Free", "Debt & portfolio tools", "Deeper advisor + scenarios", "Proactive alerts"], cta: "Start Plus", highlight: true },
    { name: "Premium", price: "$29", note: "per month", features: ["Everything in Plus", "Unlimited advisor depth", "Priority guidance", "Household accounts"], cta: "Go Premium", highlight: false },
  ];
  return (
    <section id="pricing" className="mx-auto max-w-6xl px-5 py-24">
      <Heading kicker="Pricing" title="Start free." em="Upgrade" rest="when it pays off." />
      <div className="mt-12 grid gap-4 lg:grid-cols-3">
        {plans.map((p) => (
          <Panel
            key={p.name}
            className={p.highlight ? "relative ring-glow border-brand/30" : "relative"}
          >
            {p.highlight && (
              <Badge tone="brand" className="absolute -top-3 left-5">
                Most popular
              </Badge>
            )}
            <p className="text-sm font-medium text-fg-muted">{p.name}</p>
            <p className="mt-2">
              <span className="text-4xl font-medium tracking-tight tnum">{p.price}</span>
              <span className="ml-1.5 text-sm text-fg-subtle">{p.note}</span>
            </p>
            <ul className="mt-5 space-y-2.5">
              {p.features.map((f) => (
                <li key={f} className="flex items-start gap-2 text-sm text-fg-muted">
                  <Check className="mt-0.5 size-4 shrink-0 text-brand" />
                  {f}
                </li>
              ))}
            </ul>
            <Link href="/signup" className="mt-6 block">
              <Button variant={p.highlight ? "primary" : "secondary"} className="w-full">
                {p.cta}
              </Button>
            </Link>
          </Panel>
        ))}
      </div>
    </section>
  );
}

/* ──────────────────────────────── Final CTA ─────────────────────────────── */
export function FinalCTA() {
  return (
    <section id="security" className="mx-auto max-w-6xl px-5 py-24">
      <Panel className="relative overflow-hidden px-6 py-16 text-center sm:px-16">
        <div className="absolute -top-24 left-1/2 size-72 -translate-x-1/2 rounded-full bg-brand/25 blur-[100px]" />
        <div className="relative">
          <Badge tone="brand" className="mb-6">
            <ShieldCheck className="size-3.5" /> Bank-level security, by design
          </Badge>
          <h2 className="mx-auto max-w-2xl text-balance text-4xl font-medium tracking-tight sm:text-5xl">
            Understand your money in{" "}
            <span className="font-display italic text-aurora">minutes</span>, not spreadsheets.
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-fg-muted">
            Encrypted, read-only, and grounded in your real data. Free to start — no card required.
          </p>
          <div className="mt-8 flex justify-center">
            <Link href="/signup">
              <Button size="lg">Create your free account</Button>
            </Link>
          </div>
        </div>
      </Panel>
    </section>
  );
}

/* ─────────────────────────────── Shared heading ─────────────────────────── */
function Heading({
  kicker,
  title,
  em,
  rest,
}: {
  kicker: string;
  title: string;
  em: string;
  rest: string;
}) {
  return (
    <div className="text-center">
      <span className="text-xs font-medium uppercase tracking-[0.2em] text-brand">{kicker}</span>
      <h2 className="mt-3 text-balance text-3xl font-medium tracking-tight sm:text-4xl">
        {title} <span className="font-display italic text-aurora">{em}</span> {rest}
      </h2>
    </div>
  );
}
