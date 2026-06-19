import { describe, expect, it } from "vitest";
import { humanizeTool, humanizeTools } from "./advisor-labels";

describe("humanizeTool", () => {
  it("maps known tools to friendly labels", () => {
    expect(humanizeTool("get_budget_status")).toBe("your budgets");
    expect(humanizeTool("get_spending_summary")).toBe("your spending");
  });
  it("falls back gracefully for unknown tools", () => {
    expect(humanizeTool("get_new_thing")).toBe("your new thing");
  });
});

describe("humanizeTools", () => {
  it("dedupes and joins as natural language", () => {
    expect(humanizeTools(["get_budget_status"])).toBe("your budgets");
    expect(humanizeTools(["get_budget_status", "get_goals_status"])).toBe(
      "your budgets and your goals",
    );
    expect(humanizeTools(["get_budget_status", "get_budget_status"])).toBe("your budgets");
    expect(
      humanizeTools(["get_budget_status", "get_goals_status", "get_debt_summary"]),
    ).toBe("your budgets, your goals, and your debt");
  });
});
