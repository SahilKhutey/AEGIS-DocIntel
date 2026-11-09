import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RetrievalSearch } from "@/features/intelligence/components/RetrievalSearch";

describe("RetrievalSearch", () => {
  it("submits a search query when typed", () => {
    const onSearch = vi.fn();
    render(<RetrievalSearch onSearch={onSearch} />);

    fireEvent.change(screen.getByLabelText("Search documents"), {
      target: {
        value: "indemnity liability clause",
      },
    });

    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    expect(onSearch).toHaveBeenCalledWith("indemnity liability clause");
  });

  it("disables search button when input is empty", () => {
    const onSearch = vi.fn();
    render(<RetrievalSearch onSearch={onSearch} />);

    expect(screen.getByRole("button", { name: "Search" })).toBeDisabled();
    expect(onSearch).not.toHaveBeenCalled();
  });

  it("shows searching indicator when loading", () => {
    const onSearch = vi.fn();
    render(<RetrievalSearch onSearch={onSearch} loading />);

    expect(screen.getByRole("button", { name: "Searching..." })).toBeDisabled();
  });
});
