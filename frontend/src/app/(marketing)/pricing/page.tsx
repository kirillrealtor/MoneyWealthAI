import type { Metadata } from "next";
import { PageHero } from "@/components/marketing/page-hero";
import { PricingTable } from "@/components/marketing/pricing-table";
import { Panel } from "@/components/ui/panel";

export const metadata: Metadata = {
  title: "Pricing — MoneyWealth AI",
  description: "Start free. Upgrade when it pays off. Simple monthly or annual plans, no card to begin.",
};

const FAQ = [
  { q: "Is there really a free plan?", a: "Yes. The Free plan includes every dashboard, budgets and goals, and 100 advisor messages a month — no card required to start." },
  { q: "Can I cancel anytime?", a: "Anytime, from your settings. Paid plans are month-to-month (or annual if you choose), and you keep access until the end of the period." },
  { q: "How is my financial data protected?", a: "Bank connections are read-only via Plaid, access tokens are encrypted with AES-256-GCM, and your data is isolated per account at the database level. See our Security page." },
  { q: "Does the advisor give financial advice?", a: "MoneyWealth AI provides grounded, educational information based on your real data — not personalized financial, investment, tax or legal advice." },
  { q: "What happens to my data if I cancel?", a: "You can export or delete your data anytime. Deleting your account disconnects your banks and purges your data." },
];

export default function PricingPage() {
  return (
    <main>
      <PageHero
        kicker="Pricing"
        title="Start free."
        em="Upgrade"
        rest="when it pays off."
        sub="No card to begin. Cancel anytime. Every plan is encrypted and read-only."
      />

      <section className="mx-auto max-w-5xl px-5 pb-20">
        <PricingTable />
      </section>

      <section className="mx-auto max-w-3xl px-5 pb-24">
        <h2 className="mb-6 text-center text-2xl font-medium tracking-tight">Questions, answered</h2>
        <div className="space-y-3">
          {FAQ.map((f) => (
            <Panel key={f.q} className="p-0">
              <details className="group">
                <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4 text-sm font-medium text-fg">
                  {f.q}
                  <span className="text-fg-subtle transition-transform group-open:rotate-45">+</span>
                </summary>
                <p className="px-5 pb-4 text-sm text-fg-muted">{f.a}</p>
              </details>
            </Panel>
          ))}
        </div>
      </section>
    </main>
  );
}
