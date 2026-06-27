import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Compass, ShieldCheck, Sparkles } from "lucide-react";
import { PageHero } from "@/components/marketing/page-hero";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "About — MoneyWealth AI",
  description: "Why we're building a calm, trustworthy AI financial advisor grounded in your real data.",
};

const VALUES = [
  { icon: ShieldCheck, title: "Trust before delight", body: "It holds people's money data. Accuracy, security and honesty come before flourish." },
  { icon: Sparkles, title: "Grounded, never guessed", body: "Every figure is traceable to your data. If we don't know, we say so." },
  { icon: Compass, title: "Clarity over clutter", body: "Money is stressful. One clear next step beats a wall of charts." },
];

export default function AboutPage() {
  return (
    <main>
      <PageHero
        kicker="About"
        title="Money should feel"
        em="understood,"
        rest="not overwhelming."
        sub="We're building the financial copilot we wished existed — one that reads your real numbers and tells you the truth."
      />

      <section className="mx-auto max-w-3xl px-5 pb-12">
        <Panel className="p-8">
          <p className="text-fg-muted">
            Most money apps either drown you in dashboards or hand you generic tips that ignore your
            actual situation. MoneyWealth AI takes a different path: connect your real accounts, and an AI
            advisor that <span className="text-fg">shows its work</span> turns that data into clear,
            grounded guidance — budgets, goals, debt payoff and portfolio health, all in one calm
            place.
          </p>
          <p className="mt-4 text-fg-muted">
            We hold ourselves to a higher bar than typical software, because people make real
            decisions on what they see. That means bank-level security, read-only access, and an
            advisor engineered to never invent a number.
          </p>
        </Panel>
      </section>

      <section className="mx-auto max-w-5xl px-5 pb-16">
        <div className="grid gap-4 sm:grid-cols-3">
          {VALUES.map(({ icon: Icon, title, body }) => (
            <Panel key={title}>
              <Icon className="size-6 text-brand" />
              <h2 className="mt-4 text-base font-medium">{title}</h2>
              <p className="mt-1.5 text-sm text-fg-muted">{body}</p>
            </Panel>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-3xl px-5 pb-24 text-center">
        <h2 className="text-3xl font-medium tracking-tight">Come see your money clearly.</h2>
        <div className="mt-6 flex justify-center">
          <Link href="/login">
            <Button size="lg">Start free <ArrowRight className="size-4" /></Button>
          </Link>
        </div>
      </section>
    </main>
  );
}
