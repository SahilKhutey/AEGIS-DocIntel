"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  RotateCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Layers,
  ChevronDown,
  ChevronRight,
  RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { defaultProcessingService, type ProcessingService } from "../api";
import { ProcessingTimeline } from "./processing-timeline";
import type { ProcessingJob, ProcessingJobStatus } from "../types";

export type ProcessingMonitorProps = {
  service?: ProcessingService;
  pollingIntervalMs?: number;
};

const filterTabs: Array<{ label: string; value?: ProcessingJobStatus }> = [
  { label: "All" },
  { label: "Running", value: "running" },
  { label: "Failed", value: "failed" },
  { label: "Succeeded", value: "succeeded" },
  { label: "Queued", value: "queued" },
];

function JobStatusBadge({ status }: { status: ProcessingJobStatus }) {
  switch (status) {
    case "succeeded":
      return (
        <Badge variant="success" aria-label={`Job status: Succeeded`}>
          <CheckCircle2 className="mr-1 h-3 w-3" />
          Succeeded
        </Badge>
      );
    case "running":
      return (
        <Badge variant="info" aria-label={`Job status: Running`}>
          <RotateCw className="mr-1 h-3 w-3 animate-spin" />
          Running
        </Badge>
      );
    case "failed":
      return (
        <Badge variant="danger" aria-label={`Job status: Failed`}>
          <AlertTriangle className="mr-1 h-3 w-3" />
          Failed
        </Badge>
      );
    case "retry_wait":
      return (
        <Badge variant="warning" aria-label={`Job status: Retrying`}>
          <Clock className="mr-1 h-3 w-3" />
          Retry Wait
        </Badge>
      );
    case "queued":
    default:
      return (
        <Badge variant="default" aria-label={`Job status: Queued`}>
          <Clock className="mr-1 h-3 w-3" />
          Queued
        </Badge>
      );
  }
}

export function ProcessingMonitor({
  service = defaultProcessingService,
  pollingIntervalMs = 8000,
}: ProcessingMonitorProps) {
  const [statusFilter, setStatusFilter] = useState<ProcessingJobStatus | undefined>();
  const [jobs, setJobs] = useState<ProcessingJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);

  const fetchJobs = useCallback(async () => {
    try {
      setError(null);
      const res = await service.list(statusFilter ? { status: statusFilter } : undefined);
      setJobs(res.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load processing jobs.");
    } finally {
      setLoading(false);
    }
  }, [service, statusFilter]);

  useEffect(() => {
    setLoading(true);
    fetchJobs();
  }, [fetchJobs]);

  // Polling for active jobs
  useEffect(() => {
    const hasActive = jobs.some((j) => j.status === "running" || j.status === "queued");
    if (!hasActive || pollingIntervalMs <= 0) return;

    const timer = setInterval(() => {
      fetchJobs();
    }, pollingIntervalMs);

    return () => clearInterval(timer);
  }, [jobs, fetchJobs, pollingIntervalMs]);

  async function handleRetry(jobId: string) {
    try {
      setRetryingId(jobId);
      await service.retry(jobId);
      await fetchJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to retry job.");
    } finally {
      setRetryingId(null);
    }
  }

  function toggleExpand(jobId: string) {
    setExpandedJobId((prev) => (prev === jobId ? null : jobId));
  }

  return (
    <div className="space-y-6">
      {/* Header and Control Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
            Processing Monitor
          </h1>
          <p className="text-sm text-[var(--muted)] mt-1">
            Real-time telemetry and pipeline execution tracking for document ingestion and indexing.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            setLoading(true);
            void fetchJobs();
          }}
          disabled={loading}
          aria-label="Refresh processing jobs"
        >
          <RotateCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Filter Tabs */}
      <div
        className="flex flex-wrap gap-2"
        role="group"
        aria-label="Processing job status filters"
      >
        {filterTabs.map((tab) => {
          const isActive = statusFilter === tab.value;
          return (
            <Button
              key={tab.label}
              size="sm"
              variant={isActive ? "primary" : "outline"}
              aria-pressed={isActive}
              onClick={() => setStatusFilter(tab.value)}
            >
              {tab.label}
            </Button>
          );
        })}
      </div>

      {/* Error state */}
      {error && (
        <div
          role="alert"
          className="rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 p-4 text-sm text-red-700 dark:text-red-300 flex items-center justify-between"
        >
          <span>{error}</span>
          <Button size="sm" variant="outline" onClick={() => void fetchJobs()}>
            Retry
          </Button>
        </div>
      )}

      {/* Jobs Table */}
      {loading && jobs.length === 0 ? (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-12 text-center" aria-busy="true">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-[var(--primary)] border-r-transparent" />
          <p className="mt-4 text-sm font-medium text-[var(--muted)]">Loading processing telemetry...</p>
        </div>
      ) : jobs.length === 0 ? (
        <div className="rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-12 text-center">
          <Layers className="mx-auto h-12 w-12 text-[var(--muted)]" />
          <h3 className="mt-4 text-base font-semibold text-[var(--foreground)]">No processing jobs</h3>
          <p className="mt-1 text-sm text-[var(--muted)]">
            {statusFilter
              ? `There are currently no background jobs with status "${statusFilter}".`
              : "No background processing jobs have been scheduled or run yet."}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm" aria-label="Processing jobs list">
              <thead className="border-b border-[var(--border)] bg-[var(--surface-muted)] text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
                <tr>
                  <th scope="col" className="p-4 w-8"></th>
                  <th scope="col" className="p-4">Document / Resource</th>
                  <th scope="col" className="p-4">Job Type</th>
                  <th scope="col" className="p-4">Status</th>
                  <th scope="col" className="p-4">Progress</th>
                  <th scope="col" className="p-4">Attempt</th>
                  <th scope="col" className="p-4">Updated</th>
                  <th scope="col" className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {jobs.map((job) => {
                  const isExpanded = expandedJobId === job.id;
                  const isRetrying = retryingId === job.id;

                  return (
                    <React.Fragment key={job.id}>
                      <tr
                        className={`transition-colors hover:bg-[var(--surface-muted)] cursor-pointer ${
                          isExpanded ? "bg-[var(--surface-muted)]/60" : ""
                        }`}
                        onClick={() => toggleExpand(job.id)}
                      >
                        <td className="p-4 text-[var(--muted)]">
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </td>
                        <td className="p-4">
                          <div className="font-medium text-[var(--foreground)]">
                            {job.documentName || job.documentId}
                          </div>
                          <div className="text-xs font-mono text-[var(--muted)] mt-0.5">
                            ID: {job.id}
                          </div>
                        </td>
                        <td className="p-4 text-xs font-medium text-[var(--muted)]">
                          {job.jobType.replace(/_/g, " ").toUpperCase()}
                        </td>
                        <td className="p-4">
                          <JobStatusBadge status={job.status} />
                        </td>
                        <td className="p-4 w-36">
                          <div className="flex items-center gap-2">
                            <div className="w-full bg-[var(--surface-muted)] rounded-full h-2 overflow-hidden border border-[var(--border)]">
                              <div
                                className={`h-2 rounded-full transition-all duration-300 ${
                                  job.status === "failed"
                                    ? "bg-red-500"
                                    : job.status === "succeeded"
                                      ? "bg-emerald-500"
                                      : "bg-[var(--primary)]"
                                }`}
                                style={{ width: `${job.progressPercent}%` }}
                              />
                            </div>
                            <span className="text-xs font-mono text-[var(--muted)] tabular-nums">
                              {job.progressPercent}%
                            </span>
                          </div>
                        </td>
                        <td className="p-4 text-xs text-[var(--muted)] tabular-nums">
                          {job.attempt} / {job.maxAttempts}
                        </td>
                        <td className="p-4 text-xs text-[var(--muted)] tabular-nums whitespace-nowrap">
                          {new Date(job.updatedAt).toLocaleTimeString()}
                        </td>
                        <td className="p-4 text-right" onClick={(e) => e.stopPropagation()}>
                          {job.status === "failed" && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => void handleRetry(job.id)}
                              disabled={isRetrying}
                              aria-label={`Retry failed job ${job.id}`}
                            >
                              <RefreshCw
                                className={`mr-1.5 h-3.5 w-3.5 ${
                                  isRetrying ? "animate-spin" : ""
                                }`}
                              />
                              Retry
                            </Button>
                          )}
                        </td>
                      </tr>

                      {isExpanded && job.stages && (
                        <tr className="bg-[var(--surface-muted)]/30">
                          <td colSpan={8} className="p-6">
                            <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-6 shadow-2xs">
                              <h4 className="text-sm font-semibold text-[var(--foreground)] mb-4">
                                Execution Pipeline Breakdown
                              </h4>
                              <ProcessingTimeline stages={job.stages} />
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
