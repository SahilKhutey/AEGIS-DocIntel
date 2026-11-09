import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { DocumentStatusBadge } from "@/features/documents/components/document-status";

describe("DocumentStatusBadge", () => {
  it("renders completed status with accessible label and text", () => {
    render(<DocumentStatusBadge status="completed" />);

    const badge = screen.getByLabelText("Document status: Completed");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent("Completed");
  });

  it("renders processing status with accessible label and text", () => {
    render(<DocumentStatusBadge status="processing" />);

    const badge = screen.getByLabelText("Document status: Processing");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent("Processing");
  });

  it("renders failed status with accessible label and danger appearance", () => {
    render(<DocumentStatusBadge status="failed" />);

    const badge = screen.getByLabelText("Document status: Failed");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent("Failed");
  });

  it("renders queued status with accessible label and text", () => {
    render(<DocumentStatusBadge status="queued" />);

    const badge = screen.getByLabelText("Document status: Queued");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent("Queued");
  });

  it("renders uploaded and cancelled statuses gracefully", () => {
    const { rerender } = render(<DocumentStatusBadge status="uploaded" />);
    expect(screen.getByLabelText("Document status: Uploaded")).toBeInTheDocument();

    rerender(<DocumentStatusBadge status="cancelled" />);
    expect(screen.getByLabelText("Document status: Cancelled")).toBeInTheDocument();
  });
});
