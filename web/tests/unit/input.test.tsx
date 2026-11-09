import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { Input } from "@/components/ui/input";

describe("Input", () => {
  it("renders an accessible input", () => {
    render(
      <label>
        Document name
        <Input name="documentName" />
      </label>
    );

    expect(
      screen.getByRole("textbox", { name: "Document name" })
    ).toBeInTheDocument();
  });

  it("exposes its invalid state", () => {
    render(<Input aria-label="Document name" invalid />);

    expect(screen.getByRole("textbox")).toHaveAttribute(
      "aria-invalid",
      "true"
    );
  });

  it("supports disabled state", () => {
    render(<Input aria-label="Search" disabled />);

    expect(screen.getByRole("textbox")).toBeDisabled();
  });
});
