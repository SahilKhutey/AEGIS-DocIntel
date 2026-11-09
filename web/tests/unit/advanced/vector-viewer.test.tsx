import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { VectorViewer } from "@/features/mathematics/components/VectorViewer";
import { MOCK_VECTOR_REP } from "@/features/mathematics/api/mathematics.api";

describe("VectorViewer component", () => {
  it("renders vector metadata and summary statistics", () => {
    render(<VectorViewer vector={MOCK_VECTOR_REP} />);
    expect(screen.getByText("Dense Semantic Embedding — Section 2.1")).toBeInTheDocument();
    expect(screen.getByText("1,536")).toBeInTheDocument(); // total dimensions
    expect(screen.getByText("-0.0842")).toBeInTheDocument(); // min value
    expect(screen.getByText("0.1147")).toBeInTheDocument(); // max value
  });

  it("switches to table mode and displays raw float coordinates", () => {
    render(<VectorViewer vector={MOCK_VECTOR_REP} />);
    const tableBtn = screen.getByRole("button", { name: /Table view/i });
    fireEvent.click(tableBtn);
    expect(screen.getByText("Value (Raw float32)")).toBeInTheDocument();
    expect(screen.getByText("Normalized Magnitude")).toBeInTheDocument();
  });

  it("paginates dimension subsets", () => {
    render(<VectorViewer vector={MOCK_VECTOR_REP} chunkSize={16} />);
    expect(screen.getByText(/Dimensions \[0\.\.15\]/i)).toBeInTheDocument();
    const nextBtn = screen.getByRole("button", { name: /Next dimensions/i });
    fireEvent.click(nextBtn);
    expect(screen.getByText(/Dimensions \[16\.\.31\]/i)).toBeInTheDocument();
  });
});
