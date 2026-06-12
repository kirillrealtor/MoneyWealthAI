import { TopNav } from "@/components/marketing/top-nav";
import { Footer } from "@/components/marketing/footer";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative flex min-h-dvh flex-col">
      <TopNav />
      <div id="main-content" className="flex-1">{children}</div>
      <Footer />
    </div>
  );
}
