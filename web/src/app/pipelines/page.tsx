import React from "react";
import { PipelineList } from "@/features/pipelines/components/PipelineList";

export const metadata = {
  title: "Pipeline Visualization — AEGIS-DocIntel",
  description: "Directed acyclic graph lifecycle of ingestion, extraction, and vector indexation",
};

export default function PipelinesPage() {
  return (
    <div className="space-y-6">
      <PipelineList />
    </div>
  );
}
