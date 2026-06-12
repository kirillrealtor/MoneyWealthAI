import type { Metadata } from "next";
import { Lock, ShieldCheck, Landmark, Eye, Trash2, KeyRound, ServerCog, Mail } from "lucide-react";
import { PageHero } from "@/components/marketing/page-hero";
import { Panel } from "@/components/ui/panel";

export const metadata: Metadata = {
  title: "Security — Fathom",
  description:
    "How Fathom protects your financial data: AES-256-GCM encryption, read-only bank access via Plaid, per-account isolation, and a strict web security posture.",
};

const PILLARS = [
  {
    icon: Lock,
    title: "Encrypted, always",
    body: "Bank access tokens are encrypted at rest with AES-256-GCM and bound to your account, so they can't be reused elsewhere. Traffic is TLS-only with HSTS.",
  },
  {
    icon: Landmark,
    title: "Read-only banking",
    body: "We connect through Plaid with read-only access. Fathom can see your transactions and balances — it can never move, send or withdraw your money.",
  },
  {
    icon: ShieldCheck,
    title: "Isolated by design",
    body: "Every record is isolated at the database level with row-level security, so your data is only ever reachable in your own context — defense in depth, not just app logic.",
  },
  {
    icon: KeyRound,
    title: "Tokens never exposed",
    body: "Your session's access token lives in memory only; the refresh token is an httpOnly cookie unreadable by scripts. We never put credentials in storage or URLs.",
  },
  {
    icon: ServerCog,
    title: "Hardened web layer",
    body: "A strict, nonce-based Content-Security-Policy blocks script injection, with clickjacking, MIME-sniffing and referrer protections on every response.",
  },
  {
    icon: Eye,
    title: "Grounded AI",
    body: "The advisor answers only from your data and cites what it used. It can't be prompted into leaking another user's information.",
  },
];

export default function SecurityPage() {
  return (
    <main>
      <PageHero
        kicker="Security"
        title="Built for"
        em="trust,"
        rest="from the database up."
        sub="A finance product has a higher bar. Here's exactly how your data is protected."
      />

      <section className="mx-auto max-w-5xl px-5 pb-16">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {PILLARS.map(({ icon: Icon, title, body }) => (
            <Panel key={title}>
              <Icon className="size-6 text-brand" />
              <h2 className="mt-4 text-base font-medium">{title}</h2>
              <p className="mt-1.5 text-sm text-fg-muted">{body}</p>
            </Panel>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-3xl space-y-4 px-5 pb-24">
        <Panel className="flex items-start gap-4">
          <Trash2 className="mt-0.5 size-5 shrink-0 text-brand" />
          <div>
            <h3 className="text-base font-medium">Your data, your call</h3>
            <p className="mt-1 text-sm text-fg-muted">
              Export your data anytime. Deleting your account disconnects your banks at Plaid and
              purges your data — no quiet retention.
            </p>
          </div>
        </Panel>
        <Panel className="flex items-start gap-4">
          <Mail className="mt-0.5 size-5 shrink-0 text-brand" />
          <div>
            <h3 className="text-base font-medium">Responsible disclosure</h3>
            <p className="mt-1 text-sm text-fg-muted">
              Found something? We welcome reports from security researchers. Email{" "}
              <span className="text-fg">security@fathom.app</span> and we&apos;ll respond promptly.
            </p>
          </div>
        </Panel>
      </section>
    </main>
  );
}
