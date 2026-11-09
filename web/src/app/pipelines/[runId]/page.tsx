import React from "react";
import { notFound } from "next/navigation";
import { getPipelineRunById } from "@/features/pipelines/api/pipeline.api";
import { PipelineDetail } from "@/features/pipelines/components/PipelineDetail";

export interface PipelineDetailPageProps {
  params: Promise<{ runId: string }>;
}

export default async function PipelineDetailPage({
  params,
}: PipelineDetailPageProps) {
  const { runId } = await params;
  const run = await getPipelineRunById(runId);

  if (!run) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <PipelineDetail initialRun={run} />
    </div>
  );
}
