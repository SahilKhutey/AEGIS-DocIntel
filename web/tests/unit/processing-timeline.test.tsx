import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProcessingTimeline } from "@/features/processing/components/processing-timeline";
import type { ProcessingStage } from "@/features/processing/types";

describe("ProcessingTimeline", () => {
  const sampleStages: ProcessingStage[] = [
    {
      id: "stage-1",
      name: "File Ingestion & Validation",
      status: "completed",
      durationSeconds: 1.2,
    },
    {
      id: "stage-2",
      name: "Text Extraction & OCR",
      status: "completed",
      durationSeconds: 2.8,
    },
    {
      id: "stage-3",
      name: "Chunking & Layout Analysis",
      status: "running",
    },
    {
      id: "stage-4",
      name: "Embedding & Vector Indexing",
      status: "pending",
    },
  ];

  it("renders stages in an ordered list with semantic aria-label", () => {
    render(<ProcessingTimeline stages={sampleStages} />);

    const list = screen.getByRole("list", { name: "Processing stages" });
    expect(list.tagName.toLowerCase()).toBe("ol");

    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(4);
    expect(screen.getByText("File Ingestion & Validation")).toBeInTheDocument();
    expect(screen.getByText("Embedding & Vector Indexing")).toBeInTheDocument();
  });

  it("marks running stage with aria-current='step'", () => {
    render(<ProcessingTimeline stages={sampleStages} />);

    const runningItem = screen.getByRole("listitem", { current: "step" });
    expect(runningItem).toHaveTextContent("Chunking & Layout Analysis");
  });

  it("displays error message when a stage fails", () => {
    const failedStages: ProcessingStage[] = [
      {
        id: "stage-1",
        name: "File Ingestion",
        status: "completed",
        durationSeconds: 1.0,
      },
      {
        id: "stage-2",
        name: "Text Extraction",
        status: "failed",
        errorMessage: "Corrupt PDF stream encountered at page 4",
      },
    ];

    render(<ProcessingTimeline stages={failedStages} />);

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Corrupt PDF stream encountered at page 4");
    expect(screen.getByText(/failed/i)).toBeInTheDocument();
  });

  it("computes and displays total execution time", () => {
    render(<ProcessingTimeline stages={sampleStages} />);

    // 1.2s + 2.8s = 4.0s
    expect(screen.getByText(/Total execution time: 4.0s/i)).toBeInTheDocument();
  });
});
