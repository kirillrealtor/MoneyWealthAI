import type { Metadata } from "next";
import { LegalShell } from "@/components/marketing/legal-shell";

export const metadata: Metadata = { title: "Privacy Policy — MoneyWealth AI" };

export default function PrivacyPage() {
  return (
    <LegalShell title="Privacy Policy" updated="June 2026">
      <p>
        This policy explains what we collect, why, and your choices. We collect only what&apos;s
        needed to run MoneyWealth AI and never sell your data.
      </p>
      <h2>What we collect</h2>
      <p>
        Account details (email, name), your financial data retrieved read-only via Plaid
        (transactions, balances, accounts), and product usage needed to operate and improve the
        service. Bank access tokens are encrypted at rest.
      </p>
      <h2>How we use it</h2>
      <p>
        To power your dashboards, budgets, goals and the AI advisor; to send notifications you opt
        into; and to keep the service secure. We do not sell your personal information.
      </p>
      <h2>The AI advisor</h2>
      <p>
        Your questions and relevant account data are processed to generate grounded answers. The
        advisor only accesses your own data.
      </p>
      <h2>Sharing</h2>
      <p>
        We share data only with processors that run the service (e.g. Plaid for bank connectivity,
        infrastructure and email providers) under contract, or when legally required.
      </p>
      <h2>Your rights</h2>
      <p>
        Access, export or delete your data anytime from settings. Deleting your account purges your
        data and revokes bank connections.
      </p>
      <h2>Contact</h2>
      <p>
        Questions? Email <span className="text-fg">privacy@moneywealth.ai</span>.
      </p>
    </LegalShell>
  );
}
