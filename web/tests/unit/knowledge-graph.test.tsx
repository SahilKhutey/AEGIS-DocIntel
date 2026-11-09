import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { KnowledgeGraph } from "@/features/intelligence/components/KnowledgeGraph";
import type { KnowledgeNode, KnowledgeEdge } from "@/features/intelligence/types";

describe("KnowledgeGraph", () => {
  const nodes: KnowledgeNode[] = [
    { id: "doc-1", label: "Master Agreement.pdf", type: "document", documentIds: ["doc-1"] },
    { id: "ent-1", label: "Acme Corporation", type: "entity", documentIds: ["doc-1"] },
    { id: "ent-2", label: "Indemnity Cap", type: "concept", documentIds: ["doc-1"] },
  ];

  const edges: KnowledgeEdge[] = [
    { id: "e-1", source: "ent-1", target: "doc-1", relationship: "party_to" },
    { id: "e-2", source: "ent-2", target: "doc-1", relationship: "governed_by" },
  ];

  it("renders graph controls and canvas view by default", () => {
    render(<KnowledgeGraph nodes={nodes} edges={edges} />);
    expect(screen.getByRole("button", { name: /visual graph view/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /accessible table view/i })).toBeInTheDocument();
  });

  it("switches to accessible table view when selected", () => {
    render(<KnowledgeGraph nodes={nodes} edges={edges} />);

    fireEvent.click(screen.getByRole("button", { name: /accessible table view/i }));

    expect(screen.getByText(/Accessible Knowledge Graph Table/i)).toBeInTheDocument();
    expect(screen.getByText("Acme Corporation")).toBeInTheDocument();
    expect(screen.getByText("Master Agreement.pdf")).toBeInTheDocument();
  });

  it("filters nodes when clicking node type filter button", () => {
    render(<KnowledgeGraph nodes={nodes} edges={edges} />);

    // Switch to table to easily inspect rendered rows
    fireEvent.click(screen.getByRole("button", { name: /accessible table view/i }));

    // Click "entity" filter
    const entityBtn = screen.getByRole("button", { name: "entity" });
    fireEvent.click(entityBtn);

    expect(screen.getByText("Acme Corporation")).toBeInTheDocument();
    expect(screen.queryByText("Master Agreement.pdf")).not.toBeInTheDocument();
  });
});
