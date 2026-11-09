import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ReviewQueue } from "@/features/governance/components/ReviewQueue";
import { ReviewQueueFilters } from "@/features/governance/components/ReviewQueueFilters";
import type { ReviewItem, ReviewQueueFiltersState } from "@/features/governance/types";

const mockReviewItems: ReviewItem[] = [
  {
    review_id: "rev-001",
    tenant_id: "tenant-alpha",
    candidate_id: "revenue_q3_2026",
    candidate_type: "fact",
    document_id: "doc-alpha-001",
    status: "pending",
    version: 1,
    candidate_data: {
      subject: "Acme Corporation",
      attribute: "revenue_q3_2026",
      value: "$142.5M",
      confidence: 0.98,
    },
    created_at: "2026-11-04T08:00:00Z",
    updated_at: "2026-11-04T08:00:00Z",
  },
  {
    review_id: "rev-002",
    tenant_id: "tenant-alpha",
    candidate_id: "ebitda_q3_2026",
    candidate_type: "conflict",
    document_id: "doc-alpha-002",
    status: "in_review",
    version: 2,
    candidate_data: {
      subject: "Acme Corporation",
      attribute: "ebitda_q3_2026",
      value: "$34.1M",
      confidence: 0.65,
    },
    created_at: "2026-11-04T09:00:00Z",
    updated_at: "2026-11-04T09:00:00Z",
  },
];

describe("ReviewQueue component", () => {
  it("renders review queue items correctly with attributes and status", () => {
    render(<ReviewQueue items={mockReviewItems} loading={false} />);

    expect(screen.getByText(/revenue_q3_2026/i)).toBeInTheDocument();
    expect(screen.getByText(/\$142.5M/i)).toBeInTheDocument();
    expect(screen.getByText(/ebitda_q3_2026/i)).toBeInTheDocument();
    expect(screen.getByText(/pending/i)).toBeInTheDocument();
    expect(screen.getByText(/in review/i)).toBeInTheDocument();
  });

  it("renders loading state when loading is true", () => {
    render(<ReviewQueue items={[]} loading={true} />);
    expect(screen.getByText(/loading review queue/i)).toBeInTheDocument();
  });

  it("renders empty state when items is empty", () => {
    render(<ReviewQueue items={[]} loading={false} />);
    expect(screen.getByText(/review queue is empty/i)).toBeInTheDocument();
  });
});

describe("ReviewQueueFilters component", () => {
  const defaultFilters: ReviewQueueFiltersState = {
    status: "all",
    candidateType: "all",
    assignment: "all",
    searchQuery: "",
    sortBy: "updated_at",
    sortOrder: "desc",
  };

  it("renders status tabs and triggers onChange callback", () => {
    const handleChange = vi.fn();
    render(
      <ReviewQueueFilters
        filters={defaultFilters}
        onChange={handleChange}
        countsByStatus={{ all: 10, pending: 4 }}
      />,
    );

    expect(screen.getByText("All Items")).toBeInTheDocument();
    expect(screen.getByText("Pending")).toBeInTheDocument();
  });
});
