import type { Metadata, Viewport } from "next";
import { connection } from "next/server";
import { Geist, Geist_Mono, Instrument_Serif } from "next/font/google";
import "./globals.css";
import { AuroraBackdrop } from "@/components/visual/aurora-backdrop";
import { Providers } from "@/components/providers";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });
const display = Instrument_Serif({
  variable: "--font-display",
  weight: "400",
  style: ["normal", "italic"],
  subsets: ["latin"],
});

const APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3100";
const TITLE = "Fathom — Your AI financial advisor";
const DESCRIPTION =
  "Fathom turns your real bank data into clear, grounded guidance — budgets, goals, debt and portfolio, with an AI advisor that never invents numbers.";

export const metadata: Metadata = {
  metadataBase: new URL(APP_URL),
  title: { default: TITLE, template: "%s · Fathom" },
  description: DESCRIPTION,
  applicationName: "Fathom",
  manifest: "/manifest.webmanifest",
  openGraph: {
    type: "website",
    siteName: "Fathom",
    title: TITLE,
    description: DESCRIPTION,
    url: APP_URL,
  },
  twitter: { card: "summary_large_image", title: TITLE, description: DESCRIPTION },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: "#06090f",
  colorScheme: "dark",
};

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  // Opt into dynamic rendering so the per-request CSP nonce (proxy.ts) is
  // stamped onto Next's scripts — a nonce can't be applied to a static page.
  await connection();

  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${display.variable} h-full antialiased`}
    >
      <body className="min-h-full">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-brand focus:px-4 focus:py-2 focus:font-medium focus:text-ink"
        >
          Skip to content
        </a>
        <AuroraBackdrop />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
