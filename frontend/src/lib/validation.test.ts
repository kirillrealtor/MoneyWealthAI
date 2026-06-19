import { describe, expect, it } from "vitest";
import { amountSchema, emailSchema, passwordSchema, signupSchema, validate } from "./validation";

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

describe("passwordSchema", () => {
  it("requires at least 8 characters (mirrors backend)", () => {
    expect(passwordSchema.safeParse("short").success).toBe(false);
    expect(passwordSchema.safeParse("longenough1").success).toBe(true);
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
  it("returns parsed data on success", () => {
    const r = validate(signupSchema, { email: "a@b.com", password: "password1" });
    expect(r.ok).toBe(true);
  });
  it("returns a flat field→message map on failure", () => {
    const r = validate(signupSchema, { email: "bad", password: "x" });
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.errors.email).toBeTruthy();
      expect(r.errors.password).toBeTruthy();
    }
  });
});
