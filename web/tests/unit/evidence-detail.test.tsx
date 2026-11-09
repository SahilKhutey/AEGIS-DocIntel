import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { EvidenceDetail } from "@/features/intelligence/components/EvidenceDetail";
import type { EvidenceRecord } from "@/features/intelligence/types";

describe("EvidenceDetail", () => {
  const sampleEvidence: EvidenceRecord = {
    evidenceId: "ev-test-101",
    documentId: "doc-sample-123",
    documentName: "Master Services Agreement.pdf",
    pageNumber: 14,
    section: "Section 8.2 - Indemnification",
    content: "Each party shall indemnify and hold harmless the other from any third-party claims.",
    evidenceType: "contractual_clause",
  };

  it("renders evidence details with document name, page, and content", () => {
    const onOpen = vi.fn();
    render(<EvidenceDetail evidence={sampleEvidence} onOpenDocument={onOpen} />);

    expect(screen.getByText("Master Services Agreement.pdf")).toBeInTheDocument();
    expect(screen.getByText("Page 14")).toBeInTheDocument();
    expect(screen.getByText("Section 8.2 - Indemnification")).toBeInTheDocument();
    expect(screen.getByText(/Each party shall indemnify/)).toBeInTheDocument();
  });

  it("handles missing page number gracefully", () => {
    const onOpen = vi.fn();
    const noPage = { ...sampleEvidence, pageNumber: undefined };
    render(<EvidenceDetail evidence={noPage} onOpenDocument={onOpen} />);

    expect(screen.getByText("Page reference unavailable")).toBeInTheDocument();
  });

  it("invokes onOpenDocument when clicking source document button", () => {
    const onOpen = vi.fn();
    render(<EvidenceDetail evidence={sampleEvidence} onOpenDocument={onOpen} />);

    fireEvent.click(screen.getByRole("button", { name: /open source document/i }));
    expect(onOpen).toHaveBeenCalledWith("doc-sample-123");
  });
});
