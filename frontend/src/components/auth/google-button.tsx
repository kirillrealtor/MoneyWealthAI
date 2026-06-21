"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth/context";

/* eslint-disable @typescript-eslint/no-explicit-any */
declare global {
  interface Window {
    google?: any;
  }
}

const CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
const GSI_SRC = "https://accounts.google.com/gsi/client";

/**
 * "Continue with Google" via Google Identity Services. Renders Google's official
 * button (recognizable + trusted). On success it exchanges the ID token for an
 * app session (backend verifies the token) and lands the user on the dashboard.
 * Renders nothing until NEXT_PUBLIC_GOOGLE_CLIENT_ID is configured.
 */
export function GoogleButton() {
  const ref = useRef<HTMLDivElement>(null);
  const { signInWithGoogle } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!CLIENT_ID) return;
    let cancelled = false;

    function init() {
      if (cancelled || !window.google || !ref.current) return;
      window.google.accounts.id.initialize({
        client_id: CLIENT_ID,
        callback: async (resp: { credential?: string }) => {
          if (!resp.credential) return;
          const r = await signInWithGoogle(resp.credential);
          if (r.ok) router.push("/app");
          else toast.error(r.error?.message ?? "Google sign-in failed. Please try again.");
        },
      });
      ref.current.innerHTML = "";
      window.google.accounts.id.renderButton(ref.current, {
        type: "standard",
        theme: "outline",
        size: "large",
        text: "continue_with",
        shape: "pill",
        logo_alignment: "center",
        width: 320,
      });
    }

    if (window.google) {
      init();
      return;
    }
    let script = document.querySelector<HTMLScriptElement>(`script[src="${GSI_SRC}"]`);
    if (!script) {
      script = document.createElement("script");
      script.src = GSI_SRC;
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);
    }
    script.addEventListener("load", init);
    return () => {
      cancelled = true;
      script?.removeEventListener("load", init);
    };
  }, [signInWithGoogle, router]);

  if (!CLIENT_ID) return null;
  return <div ref={ref} className="flex justify-center" aria-label="Continue with Google" />;
}

/** "or" divider + Google button — renders nothing until Google is configured. */
export function GoogleAuthSection() {
  if (!CLIENT_ID) return null;
  return (
    <div className="mt-6">
      <div className="flex items-center gap-3 text-xs text-fg-subtle">
        <span className="h-px flex-1 bg-line" />
        or
        <span className="h-px flex-1 bg-line" />
      </div>
      <div className="mt-5">
        <GoogleButton />
      </div>
    </div>
  );
}
