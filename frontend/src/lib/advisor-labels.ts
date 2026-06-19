/**
 * Humanize the advisor's tool-call names for the "checked …" citation chip.
 * Users should read "checked your budgets", not "get_budget_status".
 */
const TOOL_LABELS: Record<string, string> = {
  get_account_balances: "your account balances",
  get_budget_status: "your budgets",
  get_cash_flow: "your cash flow",
  get_debt_summary: "your debt",
  get_goals_status: "your goals",
  get_portfolio_summary: "your portfolio",
  get_spending_summary: "your spending",
};

export function humanizeTool(name: string): string {
  if (TOOL_LABELS[name]) return TOOL_LABELS[name];
  // Graceful fallback for any new/unknown tool: "get_foo_bar" → "your foo bar".
  return "your " + name.replace(/^get_/, "").replace(/_/g, " ");
}

/** Join humanized tool names into a natural-language list. */
export function humanizeTools(names: string[]): string {
  const labels = [...new Set(names.map(humanizeTool))];
  if (labels.length <= 1) return labels[0] ?? "";
  if (labels.length === 2) return `${labels[0]} and ${labels[1]}`;
  return `${labels.slice(0, -1).join(", ")}, and ${labels[labels.length - 1]}`;
}
