import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ConflictResolutionPanel } from "@/features/governance/components/ConflictResolutionPanel";
import type { ReviewItem } from "@/features/governance/types";

const mockConflictItem: ReviewItem = {
  review_id: "rev-conf-01",
  tenant_id: "tenant-01",
  candidate_id: "net_income_q3",
  candidate_type: "conflict",
  document_id: "doc-101",
  status: "in_review",
  version: 1,
  candidate_data: {
    subject: "Omega Corp",
    attribute: "net_income_q3",
    fact_1: {
      document_id: "doc-101",
      value: "$18.2M",
      evidence_quote: "Omega Corp posted net income of $18.2M in Q3 press release.",
    },
    fact_2: {
      document_id: "doc-102",
      value: "$19.1M",
      evidence_quote: "Comprehensive 10-Q filing reported net income of $19.1M after tax adjustments.",
    },
  },
  created_at: "2026-11-04T10:00:00Z",
  updated_at: "2026-11-04T10:00:00Z",
};

describe("ConflictResolutionPanel component", () => {
  it("renders both conflicting claims side by side", () => {
    render(<ConflictResolutionPanel item={mockConflictItem} />);

    expect(screen.getAllByText(/\$18.2M/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/\$19.1M/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/doc-101/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/doc-102/i).length).toBeGreaterThan(0);
  });

  it("submits conflict resolution with selected outcome and rationale", async () => {
    const handleResolve = vi.fn().mockResolvedValue(undefined);
    render(
      <ConflictResolutionPanel
        item={mockConflictItem}
        onResolveConflict={handleResolve}
      />,
    );

    const fact2Btn = screen.getByRole("button", { name: /Accept Fact 2 \(Source B\)/i });
    fireEvent.click(fact2Btn);

    const rationaleInput = screen.getByPlaceholderText(/Document the governance rationale for this cross-document resolution/i);
    fireEvent.change(rationaleInput, {
      target: { value: "10-Q filing supersedes preliminary earnings press release." },
    });

    const commitBtn = screen.getByRole("button", { name: /Commit Conflict Resolution/i });
    fireEvent.click(commitBtn);

    expect(handleResolve).toHaveBeenCalledWith({
      outcome: "accepted_second_fact",
      rationale: "10-Q filing supersedes preliminary earnings press release.",
      reconciled_value: "$19.1M",
      reconciled_evidence_quote:
        "Comprehensive 10-Q filing reported net income of $19.1M after tax adjustments.",
    });
  });
});
