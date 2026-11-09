import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MetricCard } from "@/components/advanced/MetricCard";

describe("MetricCard component", () => {
  it("renders title and formatted value", () => {
    render(<MetricCard title="Total Documents" value={142} format="number" />);
    expect(screen.getByText("Total Documents")).toBeInTheDocument();
    expect(screen.getByText("142")).toBeInTheDocument();
  });

  it("renders N/A for null values without throwing or showing 0", () => {
    render(<MetricCard title="Missing Metric" value={null} format="percent" />);
    expect(screen.getByText("Missing Metric")).toBeInTheDocument();
    expect(screen.getByText("N/A")).toBeInTheDocument();
    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });

  it("renders trend when previousValue is supplied", () => {
    render(
      <MetricCard
        title="Token Usage"
        value={1200}
        previousValue={1000}
        format="number"
      />,
    );
    expect(screen.getByLabelText("Increased by +20.0%")).toBeInTheDocument();
  });

  it("renders loading pulse placeholder when isLoading is true", () => {
    const { container } = render(
      <MetricCard title="Loading Stat" value={100} isLoading={true} />,
    );
    expect(screen.queryByText("100")).not.toBeInTheDocument();
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });
});
