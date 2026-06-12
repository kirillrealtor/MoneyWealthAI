import type { MetadataRoute } from "next";

const APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3100";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Keep the authenticated app and BFF out of search indexes.
      disallow: ["/app", "/api", "/login", "/signup"],
    },
    sitemap: `${APP_URL}/sitemap.xml`,
  };
}
