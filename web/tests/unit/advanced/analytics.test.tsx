import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AnalyticsDashboard } from "@/features/analytics/components/AnalyticsDashboard";
import { OverviewMetrics } from "@/features/analytics/components/OverviewMetrics";
import { DocumentAnalytics } from "@/features/analytics/components/DocumentAnalytics";
import { GovernanceAnalytics } from "@/features/analytics/components/GovernanceAnalytics";

describe("Analytics components", () => {
  const mockStats = {
    doc_count: 78,
    chunk_count: 1850,
    total_tokens_used: 742000,
    total_cost_usd: 11.13,
    cache_hit_rate: 64.2,
    avg_query_latency_ms: 196,
  };

  it("renders OverviewMetrics correctly with formatted stats", () => {
    render(<OverviewMetrics stats={mockStats} />);
    expect(screen.getByText("Documents")).toBeInTheDocument();
    expect(screen.getByText("78")).toBeInTheDocument();
    expect(screen.getByText("Chunks")).toBeInTheDocument();
    expect(screen.getByText("1,850")).toBeInTheDocument();
    expect(screen.getByText("742,000")).toBeInTheDocument();
    expect(screen.getByText("$11.13")).toBeInTheDocument();
    expect(screen.getByText("64.2%")).toBeInTheDocument();
    expect(screen.getByText("196ms")).toBeInTheDocument();
  });

  it("renders DocumentAnalytics with chunk density", () => {
    render(<DocumentAnalytics stats={mockStats} />);
    expect(screen.getByText("Ingestion & Chunk Density")).toBeInTheDocument();
    expect(screen.getByText("Average Chunks Per Document")).toBeInTheDocument();
    expect(screen.getByText("24 chunks/doc")).toBeInTheDocument();
    expect(screen.getByText("PDF Documents")).toBeInTheDocument();
  });

  it("renders GovernanceAnalytics with review rates", () => {
    const mockGov = {
      total_items: 84,
      approval_rate: 82.1,
      correction_rate: 11.9,
      rejection_rate: 6.0,
    };
    render(<GovernanceAnalytics metrics={mockGov} />);
    expect(screen.getByText("Total Reviewed Items")).toBeInTheDocument();
    expect(screen.getByText("84")).toBeInTheDocument();
    expect(screen.getByText("82.1%")).toBeInTheDocument();
    expect(screen.getByText("11.9%")).toBeInTheDocument();
  });

  it("renders AnalyticsDashboard tabs and switches views", async () => {
    render(<AnalyticsDashboard />);
    // Wait until data finishes loading
    await waitFor(() => {
      expect(screen.getByText("1,850")).toBeInTheDocument();
    });

    const docsTab = screen.getByRole("button", { name: /Documents & Ingestion/i });
    fireEvent.click(docsTab);
    expect(screen.getByText("Document Type Composition")).toBeInTheDocument();

    const govTab = screen.getByRole("button", { name: /Governance Reviews/i });
    fireEvent.click(govTab);
    expect(screen.getByText("Review Decision Distribution")).toBeInTheDocument();
  });
});
