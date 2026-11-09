import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AuditTimeline } from "@/features/governance/components/AuditTimeline";
import type { AuditEvent } from "@/features/governance/types";

const mockAuditEvents: AuditEvent[] = [
  {
    event_id: "evt-01",
    review_id: "rev-101",
    sequence: 1,
    tenant_id: "tenant-01",
    actor_id: "system-ingest",
    action: "create",
    previous_status: "pending",
    new_status: "pending",
    previous_version: 1,
    new_version: 1,
    rationale: "Ingested from document extraction",
    timestamp: "2026-11-04T08:00:00Z",
  },
  {
    event_id: "evt-02",
    review_id: "rev-101",
    sequence: 2,
    tenant_id: "tenant-01",
    actor_id: "reviewer_jane",
    action: "claim",
    previous_status: "pending",
    new_status: "in_review",
    previous_version: 1,
    new_version: 1,
    rationale: "Claimed by reviewer",
    timestamp: "2026-11-04T08:30:00Z",
  },
  {
    event_id: "evt-03",
    review_id: "rev-101",
    sequence: 3,
    tenant_id: "tenant-01",
    actor_id: "reviewer_jane",
    action: "approve",
    previous_status: "in_review",
    new_status: "approved",
    previous_version: 1,
    new_version: 2,
    rationale: "Numbers cross-checked with certified statements.",
    timestamp: "2026-11-04T09:00:00Z",
  },
];

describe("AuditTimeline component", () => {
  it("renders audit sequence, actor IDs, and status transitions", () => {
    render(<AuditTimeline events={mockAuditEvents} />);

    expect(screen.getByText(/#1/)).toBeInTheDocument();
    expect(screen.getByText(/#2/)).toBeInTheDocument();
    expect(screen.getByText(/#3/)).toBeInTheDocument();
    expect(screen.getAllByText("reviewer_jane").length).toBeGreaterThan(0);
    expect(screen.getByText(/Numbers cross-checked with certified statements/i)).toBeInTheDocument();
  });

  it("toggles sort order between newest first and oldest first", () => {
    render(<AuditTimeline events={mockAuditEvents} />);

    const toggleBtn = screen.getByRole("button", { name: /Newest First/i });
    expect(toggleBtn).toBeInTheDocument();

    fireEvent.click(toggleBtn);
    expect(screen.getByRole("button", { name: /Oldest First/i })).toBeInTheDocument();
  });

  it("renders empty state when no events are recorded", () => {
    render(<AuditTimeline events={[]} />);
    expect(screen.getByText(/No audit events recorded yet/i)).toBeInTheDocument();
  });
});
