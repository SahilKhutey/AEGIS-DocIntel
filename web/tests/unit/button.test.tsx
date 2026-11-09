import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "@/components/ui/button";

describe("Button", () => {
  it("renders its content", () => {
    render(<Button>Save document</Button>);

    expect(
      screen.getByRole("button", { name: "Save document" })
    ).toBeInTheDocument();
  });

  it("supports variants", () => {
    render(<Button variant="danger">Delete</Button>);

    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("disables itself when loading", () => {
    render(<Button loading>Save</Button>);

    expect(screen.getByRole("button")).toBeDisabled();
    expect(screen.getByRole("button")).toHaveAttribute("aria-busy", "true");
  });

  it("does not activate when disabled", () => {
    let called = false;

    render(
      <Button disabled onClick={() => (called = true)}>
        Submit
      </Button>
    );

    fireEvent.click(screen.getByRole("button"));

    expect(called).toBe(false);
  });
});
