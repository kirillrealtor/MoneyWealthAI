import { describe, expect, it } from "vitest";
import { amountSchema, emailSchema, loginSchema, passwordSchema, signupSchema, validate} from "./validation";

/** Shared — magic-link login and password signup/login both use emailSchema. */
describe("emailSchema", () => {
  it("accepts a valid email and trims it", () => {
    const r = emailSchema.safeParse("  user@example.com ");
    expect(r.success && r.data).toBe("user@example.com");
  });
  it("rejects malformed emails", () => {
    expect(emailSchema.safeParse("not-an-email").success).toBe(false);
    expect(emailSchema.safeParse("").success).toBe(false);
  });
});

/** Password mode — /signup and /login. */
describe("passwordSchema", () => {
  it("requires at least 8 characters (mirrors backend)", () => {
    expect(passwordSchema.safeParse("short").success).toBe(false);
    expect(passwordSchema.safeParse("longenough1").success).toBe(true);
  });
});

describe("signupSchema (password mode)", () => {
  it("accepts a valid signup payload", () => {
    expect(signupSchema.safeParse({ email: "a@b.com", password: "password1" }).success).toBe(true);
  });
  it("rejects short passwords and bad emails", () => {
    const r = signupSchema.safeParse({ email: "bad", password: "x" });
    expect(r.success).toBe(false);
  });
});

describe("loginSchema (password mode)", () => {
  it("accepts email + any non-empty password", () => {
    expect(loginSchema.safeParse({ email: "a@b.com", password: "x" }).success).toBe(true);
  });
  it("rejects empty password", () => {
    expect(loginSchema.safeParse({ email: "a@b.com", password: "" }).success).toBe(false);
  });
});

/** Magic-link mode — /login email-only form (validate(emailSchema, email)). */
describe("magic-link login validation", () => {
  it("accepts a valid email", () => {
    const r = validate(emailSchema, "user@example.com");
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.data).toBe("user@example.com");
  });
  it("returns a field error for invalid email", () => {
    const r = validate(emailSchema, "not-an-email");
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.errors._).toBeTruthy();
  });
});

describe("amountSchema", () => {
  it("accepts a well-formed positive amount", () => {
    expect(amountSchema.safeParse("10.50").success).toBe(true);
  });
  it("rejects zero, negatives, >2 decimals, and non-numeric", () => {
    expect(amountSchema.safeParse("0").success).toBe(false);
    expect(amountSchema.safeParse("-5").success).toBe(false);
    expect(amountSchema.safeParse("1.234").success).toBe(false);
    expect(amountSchema.safeParse("abc").success).toBe(false);
  });
});

describe("validate()", () => {
  it("returns parsed data on success (signup)", () => {
    const r = validate(signupSchema, { email: "a@b.com", password: "password1" });
    expect(r.ok).toBe(true);
  });
  it("returns a flat field→message map on signup failure", () => {
    const r = validate(signupSchema, { email: "bad", password: "x" });
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.errors.email).toBeTruthy();
      expect(r.errors.password).toBeTruthy();
    }
  });
});
