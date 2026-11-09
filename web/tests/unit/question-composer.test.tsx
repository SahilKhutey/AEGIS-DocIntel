import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { QuestionComposer } from "@/features/intelligence/components/QuestionComposer";

describe("QuestionComposer", () => {
  it("submits a valid question", () => {
    const onSubmit = vi.fn();
    render(<QuestionComposer onSubmit={onSubmit} />);

    fireEvent.change(screen.getByLabelText("Ask AEGIS a question"), {
      target: {
        value: "What are the key findings?",
      },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: "Ask AEGIS",
      }),
    );

    expect(onSubmit).toHaveBeenCalledWith("What are the key findings?");
  });

  it("does not submit an empty question", () => {
    const onSubmit = vi.fn();
    render(<QuestionComposer onSubmit={onSubmit} />);

    expect(
      screen.getByRole("button", {
        name: "Ask AEGIS",
      }),
    ).toBeDisabled();

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("does not submit when loading", () => {
    const onSubmit = vi.fn();
    render(<QuestionComposer onSubmit={onSubmit} isLoading />);

    expect(
      screen.getByRole("button", {
        name: "Thinking...",
      }),
    ).toBeDisabled();
  });
});
