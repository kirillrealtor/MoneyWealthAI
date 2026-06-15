import { type Page, expect } from "@playwright/test";

/**
 * Log in as the seeded demo user via the BFF — sets a fresh httpOnly refresh
 * cookie in this test's context. Each test gets its own token family, so the
 * rotating-refresh design doesn't cause cross-test revocation.
 * Requires demo@fathom.app / DemoPass123! to exist & be verified.
 */
export async function loginDemo(page: Page) {
  const res = await page.request.post("/api/auth/login", {
    data: { email: "demo@fathom.app", password: "DemoPass123!" },
  });
  expect(res.ok(), "demo login should succeed").toBeTruthy();
}
