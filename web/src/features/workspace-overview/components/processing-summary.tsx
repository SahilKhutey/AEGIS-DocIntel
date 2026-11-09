import React from "react";
import Link from "next/link";
import { Workflow, ArrowRight, RotateCw } from "lucide-react";
import type { ProcessingJob } from "@/features/processing/types";
import { Badge } from "@/components/ui/badge";

export type ProcessingSummaryProps = {
  jobs: ProcessingJob[];
};

export function ProcessingSummary({ jobs }: ProcessingSummaryProps) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
      <div className="flex items-center justify-between pb-4 border-b border-[var(--border)]">
        <div className="flex items-center gap-2">
          <Workflow className="h-5 w-5 text-[var(--primary)]" />
          <h2 className="text-base font-semibold text-[var(--foreground)]">
            Processing Summary
          </h2>
        </div>
        <Link
          href="/processing"
          className="inline-flex items-center text-xs font-semibold text-[var(--primary)] hover:underline"
        >
          View all jobs <ArrowRight className="ml-1 h-3.5 w-3.5" />
        </Link>
      </div>

      <div className="mt-4">
        {jobs.length === 0 ? (
          <p className="text-sm text-[var(--muted)] py-4 text-center">
            No background processing jobs active.
          </p>
        ) : (
          <ul className="divide-y divide-[var(--border)]">
            {jobs.slice(0, 4).map((job) => (
              <li key={job.id} className="py-3 flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-[var(--foreground)] truncate">
                    {job.documentName || job.documentId}
                  </p>
                  <p className="text-xs text-[var(--muted)]">
                    {job.currentStage || job.jobType.replace(/_/g, " ")} &middot; {job.progressPercent}%
                  </p>
                </div>
                <div>
                  {job.status === "succeeded" ? (
                    <Badge variant="success">Succeeded</Badge>
                  ) : job.status === "failed" ? (
                    <Badge variant="danger">Failed</Badge>
                  ) : job.status === "running" ? (
                    <Badge variant="info">
                      <RotateCw className="mr-1 h-3 w-3 animate-spin" />
                      Running
                    </Badge>
                  ) : (
                    <Badge variant="default">Queued</Badge>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
