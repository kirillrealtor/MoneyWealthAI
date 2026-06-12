import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Fathom — AI financial advisor",
    short_name: "Fathom",
    description:
      "Grounded AI financial guidance over your real bank data — budgets, goals, debt and portfolio.",
    start_url: "/app",
    display: "standalone",
    background_color: "#06090f",
    theme_color: "#06090f",
    icons: [
      // Provisional — replace with branded maskable 192/512 PNGs when ready.
      { src: "/favicon.ico", sizes: "48x48", type: "image/x-icon" },
    ],
  };
}
