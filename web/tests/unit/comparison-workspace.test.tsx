import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ComparisonWorkspace } from "@/features/intelligence/components/ComparisonWorkspace";
import type { DocumentItem } from "@/lib/schemas";

describe("ComparisonWorkspace", () => {
  const documents: DocumentItem[] = [
    {
      doc_id: "doc-1",
      filename: "Contract_v1.pdf",
      status: "ready",
      is_scanned: false,
      language: "en",
      created_at: "2026-11-01T00:00:00Z",
    },
    {
      doc_id: "doc-2",
      filename: "Contract_v2.pdf",
      status: "ready",
      is_scanned: false,
      language: "en",
      created_at: "2026-11-02T00:00:00Z",
    },
    {
      doc_id: "doc-3",
      filename: "Addendum.pdf",
      status: "ready",
      is_scanned: false,
      language: "en",
      created_at: "2026-11-03T00:00:00Z",
    },
  ];

  it("disables compare button when fewer than 2 documents are selected", () => {
    const onCompare = vi.fn();
    const onToggle = vi.fn();

    render(
      <ComparisonWorkspace
        documents={documents}
        selectedDocIds={["doc-1"]}
        onToggleDoc={onToggle}
        onCompare={onCompare}
      />,
    );

    expect(
      screen.getByRole("button", { name: /compare selected documents/i }),
    ).toBeDisabled();
  });

  it("enables compare button when 2 or more documents are selected", () => {
    const onCompare = vi.fn();
    const onToggle = vi.fn();

    render(
      <ComparisonWorkspace
        documents={documents}
        selectedDocIds={["doc-1", "doc-2"]}
        onToggleDoc={onToggle}
        onCompare={onCompare}
      />,
    );

    const compareBtn = screen.getByRole("button", {
      name: /compare selected documents/i,
    });
    expect(compareBtn).toBeEnabled();

    fireEvent.click(compareBtn);
    expect(onCompare).toHaveBeenCalledWith("structured");
  });

  it("calls onToggleDoc when clicking a document card", () => {
    const onCompare = vi.fn();
    const onToggle = vi.fn();

    render(
      <ComparisonWorkspace
        documents={documents}
        selectedDocIds={[]}
        onToggleDoc={onToggle}
        onCompare={onCompare}
      />,
    );

    fireEvent.click(screen.getByText("Contract_v1.pdf"));
    expect(onToggle).toHaveBeenCalledWith("doc-1");
  });
});
