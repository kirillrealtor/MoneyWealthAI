import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { Money } from "./money";

describe("<Money>", () => {
  it("shows the formatted amount visually and a screen-reader label", () => {
    const { container } = render(<Money value="-1234.5" colorize />);
    // visible (aria-hidden) text uses the true minus sign
    expect(container.querySelector("[aria-hidden]")?.textContent).toBe("−$1,234.50");
    // screen-reader text spells out the sign for assistive tech
    expect(screen.getByText(/negative/)).toBeInTheDocument();
  });

  it("applies the negative color token only when colorize is set", () => {
    const { container, rerender } = render(<Money value="-10" colorize />);
    expect(container.firstChild).toHaveClass("text-negative");
    rerender(<Money value="-10" />);
    expect(container.firstChild).not.toHaveClass("text-negative");
  });

  it("uses tabular figures for alignment", () => {
    const { container } = render(<Money value="10" />);
    expect(container.firstChild).toHaveClass("tnum");
  });
});
