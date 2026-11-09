import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PipelineGraph } from "@/features/pipelines/components/PipelineGraph";
import { PipelineStageCard } from "@/features/pipelines/components/PipelineStageCard";
import type { PipelineStage } from "@/features/pipelines/types";

describe("Pipeline Visualization components", () => {
  const mockStages: PipelineStage[] = [
    {
      id: "stage-1",
      name: "Document Ingestion",
      status: "succeeded",
      dependsOn: [],
      durationMs: 450,
      workerId: "worker-01",
    },
    {
      id: "stage-2",
      name: "OCR Vision Extraction",
      status: "failed",
      dependsOn: ["stage-1"],
      durationMs: 3000,
      workerId: "worker-02",
      error: {
        code: "TIMEOUT_EXCEEDED",
        message: "Worker exceeded deadline",
      },
    },
  ];

  it("renders stages in PipelineGraph with names and statuses", () => {
    const handleSelect = vi.fn();
    render(
      <PipelineGraph
        stages={mockStages}
        selectedStageId="stage-1"
        onSelectStage={handleSelect}
      />,
    );

    expect(screen.getByText("Document Ingestion")).toBeInTheDocument();
    expect(screen.getByText("OCR Vision Extraction")).toBeInTheDocument();
    expect(screen.getByText("450ms")).toBeInTheDocument();

    const stage2Btn = screen.getByRole("button", { name: /OCR Vision Extraction/i });
    fireEvent.click(stage2Btn);
    expect(handleSelect).toHaveBeenCalledWith("stage-2");
  });

  it("renders PipelineStageCard with duration, worker, and error details", () => {
    render(<PipelineStageCard stage={mockStages[1]} />);
    expect(screen.getByText("OCR Vision Extraction")).toBeInTheDocument();
    expect(screen.getByText("3000ms")).toBeInTheDocument();
    expect(screen.getByText("worker-02")).toBeInTheDocument();
    expect(screen.getByText("Failure Error Code: TIMEOUT_EXCEEDED")).toBeInTheDocument();
    expect(screen.getByText("Worker exceeded deadline")).toBeInTheDocument();
  });
});
