import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FactVerificationPanel } from "@/features/governance/components/FactVerificationPanel";
import type { ReviewItem } from "@/features/governance/types";

const mockFactItem: ReviewItem = {
  review_id: "rev-fact-01",
  tenant_id: "tenant-01",
  candidate_id: "gross_margin",
  candidate_type: "fact",
  document_id: "doc-101",
  status: "in_review",
  version: 1,
  candidate_data: {
    subject: "Omega Corp",
    attribute: "gross_margin",
    value: "42.8%",
    raw_value: "gross margin reached 42.8 percent",
    evidence_quote: "Omega Corp reported an expanded gross margin of 42.8% for the fiscal quarter.",
    confidence: 0.94,
  },
  created_at: "2026-11-04T10:00:00Z",
  updated_at: "2026-11-04T10:00:00Z",
};

describe("FactVerificationPanel component", () => {
  it("renders candidate statement and cited evidence quote", () => {
    render(<FactVerificationPanel item={mockFactItem} />);

    expect(screen.getByText(/Omega Corp • gross_margin/i)).toBeInTheDocument();
    expect(screen.getByText("42.8%")).toBeInTheDocument();
    expect(
      screen.getAllByText(/Omega Corp reported an expanded gross margin of 42.8%/i).length,
    ).toBeGreaterThan(0);
  });

  it("allows selecting a verification status and entering rationale", async () => {
    const handleRecord = vi.fn().mockResolvedValue(undefined);
    render(
      <FactVerificationPanel
        item={mockFactItem}
        onRecordVerification={handleRecord}
      />,
    );

    const verifiedBtn = screen.getByRole("button", { name: /Fully Verified/i });
    fireEvent.click(verifiedBtn);

    const rationaleInput = screen.getByPlaceholderText(/Explain why this verification outcome was reached/i);
    fireEvent.change(rationaleInput, { target: { value: "Directly confirmed by table on page 4." } });

    const submitBtn = screen.getByRole("button", { name: /Record Verification & Proceed/i });
    expect(submitBtn).toBeEnabled();
    fireEvent.click(submitBtn);

    expect(handleRecord).toHaveBeenCalledWith(
      {
        verification_status: "verified",
        rationale: "Directly confirmed by table on page 4.",
        verified_quote: "Omega Corp reported an expanded gross margin of 42.8% for the fiscal quarter.",
      },
      undefined,
    );
  });
});
