import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DecisionPanel } from "@/features/governance/components/DecisionPanel";
import type { ReviewItem } from "@/features/governance/types";

const mockInReviewItem: ReviewItem = {
  review_id: "rev-decision-01",
  tenant_id: "tenant-01",
  candidate_id: "operating_cashflow",
  candidate_type: "fact",
  document_id: "doc-101",
  status: "in_review",
  version: 2,
  candidate_data: {
    subject: "Omega Corp",
    attribute: "operating_cashflow",
    value: "$45.0M",
  },
  created_at: "2026-11-04T10:00:00Z",
  updated_at: "2026-11-04T10:00:00Z",
};

describe("DecisionPanel component", () => {
  it("renders action buttons and requires confirmation checkbox", async () => {
    const handleSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <DecisionPanel
        item={mockInReviewItem}
        onSubmitDecision={handleSubmit}
      />,
    );

    expect(screen.getByRole("button", { name: /^Approve/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Correct/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Reject/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Request Evidence/i })).toBeInTheDocument();

    const submitBtn = screen.getByRole("button", { name: /Submit APPROVE/i });
    expect(submitBtn).toBeDisabled();

    // Fill rationale
    const rationaleInput = screen.getByPlaceholderText(/Explain the reason for this decision/i);
    fireEvent.change(rationaleInput, { target: { value: "Verified against cash flow table." } });

    // Still disabled because checkbox not checked
    expect(submitBtn).toBeDisabled();

    // Check confirmation checkbox
    const confirmCheckbox = screen.getByRole("checkbox");
    fireEvent.click(confirmCheckbox);

    // Now enabled
    expect(submitBtn).toBeEnabled();
    fireEvent.click(submitBtn);

    expect(handleSubmit).toHaveBeenCalledWith({
      action: "approve",
      expected_version: 2,
      rationale: "Verified against cash flow table.",
      corrected_value: undefined,
      corrected_type: undefined,
      unit: undefined,
      evidence_quote: undefined,
    });
  });

  it("renders claim button when item is pending", () => {
    const pendingItem: ReviewItem = {
      ...mockInReviewItem,
      status: "pending",
    };
    const handleClaim = vi.fn();

    render(
      <DecisionPanel
        item={pendingItem}
        onSubmitDecision={vi.fn()}
        onClaim={handleClaim}
      />,
    );

    const claimBtn = screen.getByRole("button", { name: /Claim Item for Review/i });
    expect(claimBtn).toBeInTheDocument();
    fireEvent.click(claimBtn);
    expect(handleClaim).toHaveBeenCalled();
  });
});
