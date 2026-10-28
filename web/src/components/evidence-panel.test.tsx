import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { EvidencePanel } from "./evidence-panel";

describe("EvidencePanel", () => {
  it("renders an explicit empty-evidence state", () => {
    render(<EvidencePanel evidence={[]} onOpenSource={vi.fn()} />);
    expect(screen.getByText(/no supporting evidence/i)).toBeTruthy();
  });

  it("shows evidence metadata and opens the selected source", () => {
    const onOpenSource = vi.fn();
    const evidence = [
      {
        document_id: "doc-1",
        chunk_id: "chunk-4",
        quote: "Payment is due within thirty days.",
        page_number: 4,
        section_path: ["Payment", "Terms"],
      },
    ];

    render(<EvidencePanel evidence={evidence} onOpenSource={onOpenSource} />);
    expect(screen.getByText(/within thirty days/i)).toBeTruthy();
    expect(screen.getByText(/page 4/i)).toBeTruthy();
    fireEvent.click(
      screen.getByRole("button", {
        name: /open source 1/i,
      }),
    );
    expect(onOpenSource).toHaveBeenCalledWith(evidence[0]);
  });
});
