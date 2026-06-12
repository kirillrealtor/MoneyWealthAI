import type { Metadata } from "next";
import { LegalShell } from "@/components/marketing/legal-shell";

export const metadata: Metadata = { title: "Disclosures — Fathom" };

export default function DisclosuresPage() {
  return (
    <LegalShell title="Disclosures" updated="June 2026">
      <h2>Not financial advice</h2>
      <p>
        Fathom provides educational information and tools based on your data. It is not a financial
        advisor, broker-dealer, or tax or legal professional, and nothing here is personalized
        financial, investment, tax or legal advice.
      </p>
      <h2>AI-generated content</h2>
      <p>
        The advisor generates responses grounded in your data and cites what it used. AI can still
        make mistakes — verify important figures and decisions, and consult a licensed professional
        where appropriate.
      </p>
      <h2>Portfolio information</h2>
      <p>
        Portfolio features are informational only. Fathom does not recommend buying or selling any
        security and does not execute trades.
      </p>
      <h2>Bank data</h2>
      <p>
        Account data is provided read-only via Plaid and may be delayed or incomplete. Always treat
        your bank&apos;s records as the source of truth.
      </p>
    </LegalShell>
  );
}
