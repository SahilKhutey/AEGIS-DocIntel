import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DataTable } from "@/components/advanced/DataTable";

describe("DataTable component", () => {
  const sampleData = [
    { id: "1", name: "Doc Alpha", score: 95 },
    { id: "2", name: "Doc Beta", score: 80 },
    { id: "3", name: "Doc Gamma", score: 90 },
  ];

  const columns = [
    { key: "id", header: "ID" },
    { key: "name", header: "Name", sortable: true },
    { key: "score", header: "Score", sortable: true },
  ];

  it("renders table headers and rows", () => {
    render(
      <DataTable
        data={sampleData}
        columns={columns}
        keyExtractor={(row) => row.id}
      />,
    );
    expect(screen.getByText("ID")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Doc Alpha")).toBeInTheDocument();
    expect(screen.getByText("Doc Beta")).toBeInTheDocument();
  });

  it("renders empty state when data array is empty", () => {
    render(
      <DataTable
        data={[]}
        columns={columns}
        keyExtractor={(row) => (row as { id: string }).id}
      />,
    );
    expect(screen.getByText("No records found.")).toBeInTheDocument();
  });

  it("sorts rows when clicking sortable header", () => {
    render(
      <DataTable
        data={sampleData}
        columns={columns}
        keyExtractor={(row) => row.id}
      />,
    );
    const sortBtn = screen.getByRole("button", { name: /Sort by Name/i });
    fireEvent.click(sortBtn);
    const rows = screen.getAllByRole("row");
    // Row 0 is header, Row 1 should be Doc Alpha
    expect(rows[1]).toHaveTextContent("Doc Alpha");

    // Click again for descending sort
    fireEvent.click(sortBtn);
    const rowsDesc = screen.getAllByRole("row");
    expect(rowsDesc[1]).toHaveTextContent("Doc Gamma");
  });
});
