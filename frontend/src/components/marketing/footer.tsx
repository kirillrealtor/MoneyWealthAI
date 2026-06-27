import Link from "next/link";
import { Mark } from "@/components/brand/logo";

const COLUMNS = [
  {
    title: "Product",
    links: [
      { href: "/features", label: "Features" },
      { href: "/pricing", label: "Pricing" },
      { href: "/security", label: "Security" },
      { href: "/login", label: "Get started" },
    ],
  },
  {
    title: "Company",
    links: [
      { href: "/about", label: "About" },
      { href: "/security", label: "Trust" },
    ],
  },
  {
    title: "Legal",
    links: [
      { href: "/legal/terms", label: "Terms" },
      { href: "/legal/privacy", label: "Privacy" },
      { href: "/legal/disclosures", label: "Disclosures" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="mt-10 border-t border-line">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-12 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <div className="flex items-center gap-2">
            <Mark className="size-7" />
            <span className="font-display text-xl text-fg">MoneyWealth AI</span>
          </div>
          <p className="mt-3 max-w-xs text-sm text-fg-subtle">
            Your AI financial advisor — grounded in your real data, never inventing numbers.
          </p>
        </div>
        {COLUMNS.map((col) => (
          <div key={col.title}>
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-fg-subtle">
              {col.title}
            </p>
            <ul className="mt-4 space-y-2.5">
              {col.links.map((l) => (
                <li key={l.href + l.label}>
                  <Link href={l.href} className="text-sm text-fg-muted transition-colors hover:text-fg">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-5 py-6 text-xs text-fg-subtle sm:flex-row">
          <p>© {new Date().getFullYear()} MoneyWealth AI. Educational information, not financial advice.</p>
          <p>Bank connections secured by Plaid · 256-bit encryption</p>
        </div>
      </div>
    </footer>
  );
}
