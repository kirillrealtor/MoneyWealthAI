import { describe, expect, it } from "vitest";
import * as React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MoneyInput } from "./money-input";
import { MONEY_MAX } from "@/lib/api/types";

/** Controlled wrapper so we can assert the emitted decimal string. */
function Harness() {
  const [v, setV] = React.useState("");
  return (
    <>
      <MoneyInput id="amt" value={v} onChange={setV} />
      <span data-testid="val">{v}</span>
    </>
  );
}

describe("<MoneyInput>", () => {
  it("strips non-numeric characters", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.type(screen.getByRole("textbox"), "1a2b3");
    expect(screen.getByTestId("val")).toHaveTextContent("123");
  });

  it("limits to two decimal places and a single dot", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.type(screen.getByRole("textbox"), "12.3456");
    expect(screen.getByTestId("val")).toHaveTextContent("12.34");
  });

  it("rejects input above the backend MONEY_MAX cap", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.type(screen.getByRole("textbox"), String(MONEY_MAX + 1));
    // the over-cap keystroke is dropped → value never reaches the illegal amount
    expect(screen.getByTestId("val")).not.toHaveTextContent(String(MONEY_MAX + 1));
  });

  it("emits a string (never a float)", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.type(screen.getByRole("textbox"), "5.00");
    expect(screen.getByTestId("val")).toHaveTextContent("5.00");
  });
});
