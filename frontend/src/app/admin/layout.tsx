import type { Metadata } from "next";
import { AdminProvider } from "@/lib/admin/context";

export const metadata: Metadata = {
  title: "Admin · MoneyWealth AI",
  robots: { index: false, follow: false }, // never index the console
};

export default function AdminRootLayout({ children }: { children: React.ReactNode }) {
  return <AdminProvider>{children}</AdminProvider>;
}
