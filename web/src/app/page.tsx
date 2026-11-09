"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  FileText,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  Clock,
} from "lucide-react";
import { fetchWorkspaceOverview } from "@/features/workspace-overview/api";
import type { WorkspaceOverviewData } from "@/features/workspace-overview/types";
import { MetricCard } from "@/features/workspace-overview/components/metric-card";
import { RecentDocuments } from "@/features/workspace-overview/components/recent-documents";
import { ProcessingSummary } from "@/features/workspace-overview/components/processing-summary";
import { AttentionPanel } from "@/features/workspace-overview/components/attention-panel";

export default function HomePage() {
  const [data, setData] = useState<WorkspaceOverviewData | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const overview = await fetchWorkspaceOverview();
      setData(overview);
    } catch {
      // Fallback or offline graceful handling
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  return (
    <div className="space-y-8">
      {/* Hero / Header Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-800 p-8 text-white shadow-lg">
        <div className="max-w-3xl">
          <span className="inline-block rounded-full bg-white/20 px-3 py-1 text-xs font-semibold uppercase tracking-wider backdrop-blur-sm">
            Workbench v1.0 &middot; Operational Overview
          </span>
          <h1 className="mt-4 text-3xl font-extrabold sm:text-4xl tracking-tight">
            AEGIS Document Intelligence Workbench
          </h1>
          <p className="mt-3 text-base sm:text-lg text-blue-100 leading-relaxed">
            End-to-end evidence grounding, structured intelligence extraction, cross-document comparison,
            and human governance review.
          </p>
          <div className="mt-6 flex flex-wrap gap-4">
            <Link
              href="/documents"
              className="inline-flex items-center rounded-lg bg-white px-4 py-2.5 text-sm font-semibold text-blue-700 shadow hover:bg-blue-50 transition"
            >
              Document Workspace &rarr;
            </Link>
            <Link
              href="/reviews"
              className="inline-flex items-center rounded-lg border border-white/40 bg-white/10 px-4 py-2.5 text-sm font-semibold text-white hover:bg-white/20 transition backdrop-blur-sm"
            >
              Review Queue
            </Link>
          </div>
        </div>
      </div>

      {/* Operational Metrics Cards */}
      <section aria-label="Workspace metrics" className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold tracking-tight text-[var(--foreground)]">
            Workspace Operational State
          </h2>
          {loading && (
            <span className="text-xs text-[var(--muted)] flex items-center gap-1.5">
              <RotateCw className="h-3 w-3 animate-spin" /> Updating metrics...
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          <MetricCard
            label="Total Documents"
            value={data?.metrics.totalDocuments ?? 0}
            icon={<FileText className="h-4 w-4" />}
            href="/documents"
            subtext="Registered in workspace"
          />
          <MetricCard
            label="Processing"
            value={data?.metrics.processingDocuments ?? 0}
            icon={<RotateCw className="h-4 w-4" />}
            href="/processing"
            variant="info"
            subtext="Active pipeline jobs"
          />
          <MetricCard
            label="Completed"
            value={data?.metrics.completedDocuments ?? 0}
            icon={<CheckCircle2 className="h-4 w-4" />}
            href="/documents"
            variant="success"
            subtext="Indexed & ready for query"
          />
          <MetricCard
            label="Needs Attention"
            value={data?.metrics.attentionCount ?? 0}
            icon={<AlertTriangle className="h-4 w-4" />}
            variant={data && data.metrics.attentionCount > 0 ? "danger" : "default"}
            subtext={data && data.metrics.attentionCount > 0 ? "Failures requiring action" : "Zero errors"}
          />
          <MetricCard
            label="Queued"
            value={data?.metrics.queuedDocuments ?? 0}
            icon={<Clock className="h-4 w-4" />}
            href="/documents"
            subtext="Pending ingestion"
          />
        </div>
      </section>

      {/* Attention Alert Panel (if any items) */}
      {data && data.attentionItems.length > 0 && (
        <section aria-label="Items requiring attention">
          <AttentionPanel items={data.attentionItems} />
        </section>
      )}

      {/* Activity Feeds Grid */}
      <section aria-label="Recent activity" className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentDocuments documents={data?.recentDocuments || []} />
        <ProcessingSummary jobs={data?.recentJobs || []} />
      </section>

      {/* Capability Modules Navigation */}
      <section aria-label="Workbench capabilities" className="pt-2">
        <h2 className="text-lg font-bold tracking-tight text-[var(--foreground)] mb-4">
          Workbench Capabilities
        </h2>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
            <div className="text-2xl mb-2">📄</div>
            <h3 className="text-base font-semibold text-[var(--foreground)]">Document Workspace</h3>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Upload, inspect indexing pipelines, view text chunks, and track processing states.
            </p>
            <Link href="/documents" className="mt-4 inline-block text-sm font-medium text-[var(--primary)] hover:underline">
              Manage documents &rarr;
            </Link>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
            <div className="text-2xl mb-2">💬</div>
            <h3 className="text-base font-semibold text-[var(--foreground)]">Ask &amp; Evidence Explorer</h3>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Ask questions over authorized documents and inspect strictly cited evidence snippets.
            </p>
            <Link href="/ask" className="mt-4 inline-block text-sm font-medium text-[var(--primary)] hover:underline">
              Start query &rarr;
            </Link>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
            <div className="text-2xl mb-2">⚖️</div>
            <h3 className="text-base font-semibold text-[var(--foreground)]">Intelligence &amp; Compare</h3>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Compare multi-document agreements, extract typed facts, and detect contradictions.
            </p>
            <Link href="/compare" className="mt-4 inline-block text-sm font-medium text-[var(--primary)] hover:underline">
              Compare agreements &rarr;
            </Link>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
            <div className="text-2xl mb-2">🛡️</div>
            <h3 className="text-base font-semibold text-[var(--foreground)]">Human Review &amp; Audit</h3>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Review candidate facts and conflicts, submit versioned decisions, and record audit trails.
            </p>
            <Link href="/reviews" className="mt-4 inline-block text-sm font-medium text-[var(--primary)] hover:underline">
              Open review queue &rarr;
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
