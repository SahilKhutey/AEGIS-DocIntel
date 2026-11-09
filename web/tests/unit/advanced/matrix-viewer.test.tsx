import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MatrixViewer } from "@/features/mathematics/components/MatrixViewer";
import { MOCK_MATRIX_REP } from "@/features/mathematics/api/mathematics.api";

describe("MatrixViewer component", () => {
  it("renders matrix dimensions and condition number", () => {
    render(<MatrixViewer matrix={MOCK_MATRIX_REP} />);
    expect(screen.getByText("Document Inter-Chunk Cosine Similarity Kernel")).toBeInTheDocument();
    expect(screen.getByText(/8 × 8 matrix/i)).toBeInTheDocument();
    expect(screen.getByText(/Condition No: 2.45/i)).toBeInTheDocument();
  });

  it("selects a cell on click and displays precise row, col, and value", () => {
    render(<MatrixViewer matrix={MOCK_MATRIX_REP} />);
    expect(screen.getByText("Click any cell to inspect value")).toBeInTheDocument();

    const cells = screen.getAllByTitle(/\[0, 1\]/i);
    expect(cells.length).toBeGreaterThan(0);
    fireEvent.click(cells[0]);

    expect(screen.getByText("Selected:")).toBeInTheDocument();
    expect(screen.getByText(/Row 0/i)).toBeInTheDocument();
    expect(screen.getByText(/Col 1/i)).toBeInTheDocument();
    expect(screen.getByText("0.8400")).toBeInTheDocument();
  });
});
