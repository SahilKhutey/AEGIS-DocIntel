import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { EquationRenderer } from "@/features/mathematics/components/EquationRenderer";
import { STANDARD_EQUATIONS } from "@/features/mathematics/api/mathematics.api";

describe("EquationRenderer component", () => {
  it("renders equation title, LaTeX string, and category badge", () => {
    const eq = STANDARD_EQUATIONS[0];
    render(<EquationRenderer equation={eq} />);
    expect(screen.getByText("Cosine Similarity Metric")).toBeInTheDocument();
    expect(screen.getByText("similarity")).toBeInTheDocument();
    expect(screen.getByText(eq.latex)).toBeInTheDocument();
  });

  it("renders variables and explanations list", () => {
    const eq = STANDARD_EQUATIONS[0];
    render(<EquationRenderer equation={eq} />);
    expect(screen.getByText(/Embedding Vectors/i)).toBeInTheDocument();
    expect(screen.getByText(/Euclidean Norm/i)).toBeInTheDocument();
    expect(screen.getByText(/Dimensionality/i)).toBeInTheDocument();
  });
});
