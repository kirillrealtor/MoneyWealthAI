import type { Metadata } from "next";
import { LegalShell } from "@/components/marketing/legal-shell";

export const metadata: Metadata = { title: "Terms of Service — Fathom" };

export default function TermsPage() {
  return (
    <LegalShell title="Terms of Service" updated="June 2026">
      <p>
        These Terms govern your use of Fathom. By creating an account, you agree to them. Fathom
        provides educational financial information and tools; it does not provide financial,
        investment, tax or legal advice.
      </p>
      <h2>Your account</h2>
      <p>
        You are responsible for keeping your credentials secure and for activity under your account.
        You must provide accurate information and be at least 18 years old.
      </p>
      <h2>Acceptable use</h2>
      <p>
        Don&apos;t misuse the service: no attempts to breach security, access other users&apos; data,
        scrape at scale, or use Fathom for unlawful purposes.
      </p>
      <h2>Bank connections</h2>
      <p>
        Bank data is accessed read-only through Plaid under their terms. You authorize Fathom to
        retrieve and display your account information to power the product.
      </p>
      <h2>No financial advice</h2>
      <p>
        Outputs — including the AI advisor — are informational only. You are responsible for your own
        financial decisions. Consult a licensed professional for advice.
      </p>
      <h2>Termination</h2>
      <p>
        You may close your account anytime. We may suspend accounts that violate these Terms. On
        deletion, your data is purged and bank connections revoked.
      </p>
      <h2>Changes</h2>
      <p>We may update these Terms; we&apos;ll notify you of material changes.</p>
    </LegalShell>
  );
}
