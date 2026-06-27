import { type Page, expect } from "@playwright/test";

const DEMO_EMAIL = "demo@fathom.app";
const API_BASE = process.env.E2E_API_BASE_URL || "http://localhost:3000";

/**
 * Log in as the seeded demo user via magic link — sets a fresh httpOnly refresh
 * cookie in this test's context. Requires demo@fathom.app to exist (any auth provider).
 */
export async function loginDemo(page: Page) {
  await page.request.post("/api/auth/magic-link", { data: { email: DEMO_EMAIL } });

  const peek = await page.request.get(
    `${API_BASE}/api/v1/auth/dev/peek-magic-link?email=${encodeURIComponent(DEMO_EMAIL)}`,
  );
  expect(peek.ok(), "dev peek-magic-link should succeed").toBeTruthy();
  const { token } = (await peek.json()) as { token: string };

  const verify = await page.request.get(`/api/auth/verify-email?token=${encodeURIComponent(token)}`);
  expect(verify.ok(), "verify-email should succeed").toBeTruthy();
}
