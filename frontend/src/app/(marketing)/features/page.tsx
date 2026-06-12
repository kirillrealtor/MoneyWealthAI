import type { Metadata } from "next";
import Link from "next/link";
import {
  Sparkles,
  Wallet,
  Target,
  TrendingDown,
  PieChart,
  BellRing,
  Check,
  ArrowRight,
} from "lucide-react";
import { PageHero } from "@/components/marketing/page-hero";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Features — Fathom",
  description:
    "A grounded AI advisor, budgets, goals, debt payoff, portfolio and proactive alerts — one calm app for every money decision.",
};

const FEATURES = [
  {
    icon: Sparkles,
    name: "AI Advisor",
    tag: "Grounded, cited, honest",
    body: "Ask anything about your money in plain language. Fathom reads your real transactions, budgets and accounts, answers with the exact figures, and shows you what it checked — and tells you honestly when it doesn't know.",
    points: ["Cites the data behind every answer", "Never invents balances or numbers", "Streams replies in real time"],
  },
  {
    icon: Wallet,
    name: "Budgets",
    tag: "Know before month-end",
    body: "Set a monthly limit per category and watch your pace live. Fathom warns you as you approach a limit — not after you've blown past it.",
    points: ["Live pacing vs. limit", "Approaching-limit alerts", "Real Plaid categories"],
  },
  {
    icon: Target,
    name: "Goals",
    tag: "Reverse-engineered for you",
    body: "Name a target and a date; we work out the exact monthly amount to get there and track your progress, flagging when you drift off pace.",
    points: ["Auto monthly target", "On-track / behind signals", "Progress at a glance"],
  },
  {
    icon: TrendingDown,
    name: "Debt payoff",
    tag: "Snowball vs. avalanche",
    body: "See your debt-free date, compare strategies side by side, and watch how an extra payment changes the interest you'll pay.",
    points: ["Payoff timeline", "Interest saved, quantified", "Add-a-payment what-ifs"],
  },
  {
    icon: PieChart,
    name: "Portfolio",
    tag: "Clarity, not trade tips",
    body: "Allocation, drift and concentration at a glance, with unrealized P/L — purely informational, never a directive to buy or sell.",
    points: ["Allocation & sector exposure", "Concentration flags", "Rebalance gaps"],
  },
  {
    icon: BellRing,
    name: "Proactive alerts",
    tag: "Quiet, respectful",
    body: "Overspend, unusual charges and goal milestones reach you the moment they matter — and stay silent during your quiet hours.",
    points: ["Unusual-transaction detection", "Goal milestones", "Quiet hours & channel control"],
  },
];

export default function FeaturesPage() {
  return (
    <main>
      <PageHero
        kicker="Features"
        title="A whole financial team,"
        em="one"
        rest="calm app."
        sub="Every surface answers a real question about your money — and the advisor ties it all together."
      />

      <section className="mx-auto max-w-5xl space-y-5 px-5 pb-20">
        {FEATURES.map(({ icon: Icon, name, tag, body, points }, i) => (
          <Panel key={name} className="grid gap-6 p-8 md:grid-cols-[1fr_1.4fr] md:items-center">
            <div className={i % 2 ? "md:order-2" : ""}>
              <div className="flex size-12 items-center justify-center rounded-2xl bg-brand/10 ring-1 ring-brand/20">
                <Icon className="size-6 text-brand" />
              </div>
              <p className="mt-4 text-xs font-medium uppercase tracking-[0.18em] text-fg-subtle">{tag}</p>
              <h2 className="mt-1 text-2xl font-medium tracking-tight">{name}</h2>
            </div>
            <div className={i % 2 ? "md:order-1" : ""}>
              <p className="text-fg-muted">{body}</p>
              <ul className="mt-4 grid gap-2 sm:grid-cols-3">
                {points.map((p) => (
                  <li key={p} className="flex items-start gap-1.5 text-sm text-fg-muted">
                    <Check className="mt-0.5 size-4 shrink-0 text-brand" />
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          </Panel>
        ))}
      </section>

      <section className="mx-auto max-w-3xl px-5 pb-24 text-center">
        <h2 className="text-3xl font-medium tracking-tight">Ready to see it on your numbers?</h2>
        <div className="mt-6 flex justify-center">
          <Link href="/signup">
            <Button size="lg">Start free <ArrowRight className="size-4" /></Button>
          </Link>
        </div>
      </section>
    </main>
  );
}
