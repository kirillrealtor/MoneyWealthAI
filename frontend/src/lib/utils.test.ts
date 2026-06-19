import { describe, expect, it } from "vitest";
import { cn, formatMoney } from "./utils";

describe("formatMoney", () => {
  it("formats a positive decimal string with currency + grouping", () => {
    expect(formatMoney("1234.5")).toBe("$1,234.50");
  });

  it("renders negatives with a true minus sign (U+2212), not a hyphen", () => {
    expect(formatMoney("-1234.5")).toBe("−$1,234.50");
  });

  it("treats string and number inputs identically (no float drift entry point)", () => {
    expect(formatMoney("99.99")).toBe(formatMoney(99.99));
  });

  it("adds explicit +/- when signed", () => {
    expect(formatMoney("50", "USD", { signed: true })).toBe("+$50.00");
    expect(formatMoney("-50", "USD", { signed: true })).toBe("−$50.00");
  });

  it("compacts large values", () => {
    expect(formatMoney("1500000", "USD", { compact: true })).toBe("$1.5M");
  });

  it("respects the currency argument", () => {
    expect(formatMoney("10", "EUR")).toContain("10");
    expect(formatMoney("10", "EUR")).not.toBe(formatMoney("10", "USD"));
  });
});

describe("cn", () => {
  it("merges conditional classes and de-dupes Tailwind conflicts", () => {
    expect(cn("p-2", "p-4")).toBe("p-4");
    expect(cn("text-sm", false && "hidden", "font-bold")).toBe("text-sm font-bold");
  });
});
