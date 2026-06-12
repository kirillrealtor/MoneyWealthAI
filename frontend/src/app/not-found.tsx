import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Mark } from "@/components/brand/logo";

export default function NotFound() {
  return (
    <main className="grid min-h-dvh place-items-center px-5 text-center">
      <div className="animate-[rise_0.5s_ease-out_both]">
        <Mark className="mx-auto size-10" />
        <p className="mt-6 font-display text-7xl italic text-aurora">404</p>
        <h1 className="mt-2 text-2xl font-medium tracking-tight">This page wandered off.</h1>
        <p className="mt-2 text-fg-muted">The link may be broken or the page may have moved.</p>
        <div className="mt-7 flex justify-center gap-3">
          <Link href="/">
            <Button variant="secondary">Back home</Button>
          </Link>
          <Link href="/app">
            <Button>Go to app</Button>
          </Link>
        </div>
      </div>
    </main>
  );
}
