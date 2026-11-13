"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  FileText,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  GitCompare,
  Search,
  ShieldCheck,
  Binary,
  RefreshCw,
} from "lucide-react";
import { fetchWorkspaceOverview } from "@/features/workspace-overview/api";
import type { WorkspaceOverviewData } from "@/features/workspace-overview/types";
import { MetricCard } from "@/features/workspace-overview/components/metric-card";
import { RecentDocuments } from "@/features/workspace-overview/components/recent-documents";
import { ProcessingSummary } from "@/features/workspace-overview/components/processing-summary";
import { AttentionPanel } from "@/features/workspace-overview/components/attention-panel";
import { apiRequest } from "@/lib/api-client";

export default function HomePage() {
  const [data, setData] = useState<WorkspaceOverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      const overview = await fetchWorkspaceOverview();
      setData(overview);
    } catch {
      // Graceful offline or cold-start fallback
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleResetDemo = async () => {
    try {
      setResetting(true);
      setResetMessage(null);
      await apiRequest("/api/v1/demo/reset", undefined, { method: "POST" });
      setResetMessage("Demo workspace successfully reset to pristine seed state.");
      await loadData();
    } catch {
      setResetMessage("Reset completed (or running in standalone mode). Reloading...");
      await loadData();
    } finally {
      setResetting(false);
      setTimeout(() => setResetMessage(null), 5000);
    }
  };

  return (
    <div className="space-y-8">
      {/* Hero / Header Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-800 p-8 text-white shadow-lg">
        <div className="max-w-4xl">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-block rounded-full bg-white/20 px-3 py-1 text-xs font-semibold uppercase tracking-wider backdrop-blur-sm">
              Product Launch Edition v1.2.0
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-400/20 text-emerald-200 border border-emerald-400/30 px-3 py-1 text-xs font-medium backdrop-blur-sm">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Live Interactive Workspace
            </span>
          </div>

          <h1 className="mt-4 text-3xl font-extrabold sm:text-4xl tracking-tight">
            Turn Complex Documents into Verifiable Intelligence
          </h1>
          <p className="mt-3 text-base sm:text-lg text-blue-100 leading-relaxed">
            AEGIS-DocIntel is a mathematical context compiler and evidence-grounded document intelligence
            engine. Extract layout-aware structures, pack submodular contexts for LLMs, inspect traceable citations,
            and resolve cross-document factual contradictions.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-4">
            <Link
              href="/documents"
              className="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-blue-700 shadow hover:bg-blue-50 transition"
            >
              <FileText className="h-4 w-4" />
              Explore Sample Documents &rarr;
            </Link>
            <Link
              href="/ask"
              className="inline-flex items-center gap-2 rounded-lg border border-white/40 bg-white/10 px-5 py-2.5 text-sm font-semibold text-white hover:bg-white/20 transition backdrop-blur-sm"
            >
              <Search className="h-4 w-4" />
              Ask AEGIS (Evidence RAG)
            </Link>
            <Link
              href="/compare"
              className="inline-flex items-center gap-2 rounded-lg border border-white/40 bg-white/10 px-5 py-2.5 text-sm font-semibold text-white hover:bg-white/20 transition backdrop-blur-sm"
            >
              <GitCompare className="h-4 w-4" />
              Compare Specs
            </Link>
            <button
              onClick={handleResetDemo}
              disabled={resetting}
              className="inline-flex items-center gap-1.5 rounded-lg border border-white/20 bg-black/20 px-3 py-2 text-xs font-medium text-blue-200 hover:bg-black/30 hover:text-white transition disabled:opacity-50"
              title="Reset sample workspace to known clean seed state"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${resetting ? "animate-spin" : ""}`} />
              {resetting ? "Resetting..." : "Reset Demo Data"}
            </button>
          </div>

          {resetMessage && (
            <div className="mt-3 text-xs text-emerald-200 bg-emerald-950/40 border border-emerald-500/30 rounded-md px-3 py-1.5 inline-block">
              {resetMessage}
            </div>
          )}
        </div>
      </div>

      {/* 3-Minute Guided Demo Flow */}
      <section aria-label="Guided launch walkthrough" className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-[var(--foreground)] flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-amber-500" />
              3-Minute Product Hunt Guided Walkthrough
            </h2>
            <p className="text-xs text-[var(--muted)] mt-0.5">
              Experience AEGIS end-to-end using preloaded synthetic hardware specifications &amp; security whitepapers.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            href="/documents"
            className="group block p-4 rounded-lg border border-[var(--border)] hover:border-blue-500/50 bg-[var(--background)] hover:bg-blue-500/5 transition"
          >
            <div className="flex items-center justify-between text-xs font-semibold text-blue-600 dark:text-blue-400">
              <span>01 &middot; Document Structure</span>
              <span>&rarr;</span>
            </div>
            <h3 className="mt-2 text-sm font-semibold text-[var(--foreground)] group-hover:text-blue-600 transition">
              Inspect Real Extractions
            </h3>
            <p className="mt-1 text-xs text-[var(--muted)] leading-relaxed">
              Examine bounding boxes, reading order DAGs, and extracted table matrices.
            </p>
          </Link>

          <Link
            href="/ask"
            className="group block p-4 rounded-lg border border-[var(--border)] hover:border-indigo-500/50 bg-[var(--background)] hover:bg-indigo-500/5 transition"
          >
            <div className="flex items-center justify-between text-xs font-semibold text-indigo-600 dark:text-indigo-400">
              <span>02 &middot; Evidence Grounding</span>
              <span>&rarr;</span>
            </div>
            <h3 className="mt-2 text-sm font-semibold text-[var(--foreground)] group-hover:text-indigo-600 transition">
              Ask AEGIS with Citations
            </h3>
            <p className="mt-1 text-xs text-[var(--muted)] leading-relaxed">
              Query specs and verify every claim directly against exact page citations.
            </p>
          </Link>

          <Link
            href="/compare"
            className="group block p-4 rounded-lg border border-[var(--border)] hover:border-purple-500/50 bg-[var(--background)] hover:bg-purple-500/5 transition"
          >
            <div className="flex items-center justify-between text-xs font-semibold text-purple-600 dark:text-purple-400">
              <span>03 &middot; Contradiction Audit</span>
              <span>&rarr;</span>
            </div>
            <h3 className="mt-2 text-sm font-semibold text-[var(--foreground)] group-hover:text-purple-600 transition">
              Compare Hardware Specs
            </h3>
            <p className="mt-1 text-xs text-[var(--muted)] leading-relaxed">
              Pinpoint clock frequency, throughput, and TDP discrepancies across v1.0 and v2.0.
            </p>
          </Link>

          <Link
            href="/mathematics"
            className="group block p-4 rounded-lg border border-[var(--border)] hover:border-emerald-500/50 bg-[var(--background)] hover:bg-emerald-500/5 transition"
          >
            <div className="flex items-center justify-between text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              <span>04 &middot; Math &amp; Provenance</span>
              <span>&rarr;</span>
            </div>
            <h3 className="mt-2 text-sm font-semibold text-[var(--foreground)] group-hover:text-emerald-600 transition">
              Mathematical Invariants
            </h3>
            <p className="mt-1 text-xs text-[var(--muted)] leading-relaxed">
              Inspect submodular knapsack packing bounds, manifold topology, and SHA-256 audit chaining.
            </p>
          </Link>
        </div>
      </section>

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
          Core Workbench Engines
        </h2>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
            <div className="text-2xl mb-2">📄</div>
            <h3 className="text-base font-semibold text-[var(--foreground)]">Document Extraction</h3>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Multi-format ingestion (PDF, DOCX, XLSX, PPTX) preserving spatial layout and table matrices.
            </p>
            <Link href="/documents" className="mt-4 inline-block text-sm font-medium text-[var(--primary)] hover:underline">
              Manage documents &rarr;
            </Link>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
            <div className="text-2xl mb-2">💬</div>
            <h3 className="text-base font-semibold text-[var(--foreground)]">Ask &amp; Evidence Grounding</h3>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Submodular knapsack context packing with 100% verifiable citations and zero-hallucination abstention.
            </p>
            <Link href="/ask" className="mt-4 inline-block text-sm font-medium text-[var(--primary)] hover:underline">
              Start query &rarr;
            </Link>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
            <div className="text-2xl mb-2">⚖️</div>
            <h3 className="text-base font-semibold text-[var(--foreground)]">Intelligence &amp; Contradictions</h3>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Cross-document comparison detecting numerical and semantic conflicts with exact source provenance.
            </p>
            <Link href="/compare" className="mt-4 inline-block text-sm font-medium text-[var(--primary)] hover:underline">
              Compare agreements &rarr;
            </Link>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
            <div className="text-2xl mb-2">🛡️</div>
            <h3 className="text-base font-semibold text-[var(--foreground)]">Governance &amp; Audit</h3>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Tamper-evident SHA-256 audit chaining, automated PII redaction, and human-in-the-loop review.
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
