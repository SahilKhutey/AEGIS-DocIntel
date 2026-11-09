"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import {
  FactVerificationPanel,
  ConflictResolutionPanel,
  DecisionPanel,
  AuditTimeline,
  QualityFeedbackForm,
} from "@/features/governance/components";
import { useGovernanceDetail } from "@/features/governance/hooks/useGovernance";
import { submitVerificationAsDecision } from "@/features/governance/api/verification.api";
import { submitConflictResolutionAsDecision } from "@/features/governance/api/conflict.api";
import { getStatusStyle, calculatePriority, PRIORITY_CONFIG } from "@/features/governance/utils/review-status";
import { ErrorState } from "@/components/error-state";
import type { FactVerificationInput } from "@/features/governance/schemas/verification.schema";
import type { ConflictResolutionInput } from "@/features/governance/schemas/conflict.schema";

interface PageProps {
  params: Promise<{ reviewId: string }>;
}

type TabKey = "overview" | "verification" | "conflicts" | "decisions" | "audit" | "feedback";

function ReviewDetailContent({ params }: PageProps) {
  const { reviewId } = use(params);

  const {
    item,
    history,
    loading,
    submitting,
    error,
    staleWarning,
    successMessage,
    reload,
    claim,
    submitDecision,
    reopen,
    sendFeedback,
    setSuccessMessage,
  } = useGovernanceDetail(reviewId);

  const [activeTab, setActiveTab] = useState<TabKey>("overview");

  useEffect(() => {
    reload(true);
  }, [reload]);

  if (loading) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-12 text-center" aria-busy="true">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent" />
        <p className="mt-4 text-sm font-medium text-gray-600">Loading review item...</p>
      </div>
    );
  }

  if (error && !item) {
    return (
      <div className="space-y-4">
        <Link href="/reviews" className="text-sm font-medium text-blue-600 hover:underline">
          &larr; Back to Review Queue
        </Link>
        <ErrorState title="Review Inaccessible" message={error} onRetry={reload} />
      </div>
    );
  }

  if (!item) return null;

  const candidate = (item.candidate_data || {}) as Record<string, unknown>;
  const subjectStr = String(candidate.subject || "Fact");
  const attributeStr = String(candidate.attribute || item.candidate_id || item.review_id);
  const statusStyle = getStatusStyle(item.status);
  const priority = calculatePriority(
    item.confidence ??
      (typeof candidate.confidence === "number" ? candidate.confidence : undefined),
  );
  const priorityStyle = PRIORITY_CONFIG[priority];
  const isConflict = item.candidate_type === "conflict";

  async function handleRecordVerification(
    verificationInput: FactVerificationInput,
    correctedValue?: string,
  ) {
    if (!item) return;
    await submitVerificationAsDecision({
      reviewItem: item,
      verificationInput,
      correctedValue,
    });
    setSuccessMessage("Verification recorded successfully.");
    await reload(false);
  }

  async function handleResolveConflict(conflictInput: ConflictResolutionInput) {
    if (!item) return;
    await submitConflictResolutionAsDecision({
      reviewItem: item,
      conflictInput,
    });
    setSuccessMessage("Conflict resolution recorded successfully.");
    await reload(false);
  }

  return (
    <div className="space-y-6" data-testid="review-detail-page">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/reviews" className="hover:text-blue-600">
          Review Queue
        </Link>
        <span>/</span>
        <span className="text-gray-900 font-medium truncate max-w-sm">
          {subjectStr} &bull; {attributeStr}
        </span>
      </div>

      {/* Stale Version Alert */}
      {staleWarning && (
        <div role="alert" className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-amber-900">
          <div className="flex items-center justify-between">
            <div className="text-sm">
              <span className="font-bold">⚠️ Stale review version detected!</span> Another reviewer has modified this item. Please reload to inspect the latest state.
            </div>
            <button
              type="button"
              onClick={() => reload()}
              className="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-700"
            >
              Reload Latest
            </button>
          </div>
        </div>
      )}

      {/* Success Notification */}
      {successMessage && (
        <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          {successMessage}
        </div>
      )}

      {error && <ErrorState title="Review Action Error" message={error} onRetry={reload} />}

      {/* Review Header Banner */}
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
                {subjectStr} &bull; {attributeStr}
              </h1>
              <span
                className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium border ${statusStyle.bg} ${statusStyle.text} ${statusStyle.border}`}
              >
                <span className={`h-1.5 w-1.5 rounded-full ${statusStyle.dot}`} />
                {statusStyle.label}
              </span>
              <span
                className={`inline-flex rounded px-2 py-0.5 text-xs font-medium border ${priorityStyle.bg} ${priorityStyle.text} ${priorityStyle.border}`}
              >
                {priorityStyle.label}
              </span>
              <span className="rounded bg-gray-100 text-gray-600 text-xs font-mono uppercase px-2 py-0.5">
                {item.candidate_type}
              </span>
            </div>
            <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-500 font-mono">
              <span>Review ID: {item.review_id}</span>
              <span>&bull;</span>
              <span>Version: v{item.version}</span>
              {item.assigned_to && (
                <>
                  <span>&bull;</span>
                  <span className="text-gray-700 font-sans font-medium">Assigned: {item.assigned_to}</span>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {(item.status === "pending" || item.status === "needs_evidence") && (
              <button
                type="button"
                onClick={claim}
                disabled={submitting}
                className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-blue-500 disabled:opacity-50"
              >
                Claim Item
              </button>
            )}
            <Link
              href="/reviews"
              className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50"
            >
              &larr; Queue
            </Link>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap items-center gap-1 border-t border-gray-100 pt-3" role="tablist">
          {[
            { id: "overview", label: "Overview" },
            { id: "verification", label: "Fact Verification" },
            ...(isConflict ? [{ id: "conflicts", label: "Conflict Resolution" }] : []),
            { id: "decisions", label: "Decision Management" },
            { id: "audit", label: `Audit Trail (${history.length})` },
            { id: "feedback", label: "Quality Feedback" },
          ].map((t) => {
            const isActive = activeTab === t.id;
            return (
              <button
                key={t.id}
                role="tab"
                aria-selected={isActive}
                type="button"
                onClick={() => setActiveTab(t.id as TabKey)}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                  isActive
                    ? "bg-blue-600 text-white shadow-xs"
                    : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                {t.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Content: Overview */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Original Inferred State */}
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs space-y-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                Original System Extraction
              </span>
              <div>
                <span className="text-xs text-gray-500">Extracted Value:</span>
                <p className="text-base font-semibold text-gray-900 font-mono mt-0.5">
                  {String(candidate.value ?? candidate.raw_value ?? item.extracted_value ?? "—")}
                </p>
              </div>
              {Boolean(candidate.raw_value) && (
                <div>
                  <span className="text-xs text-gray-500">Raw Source Text:</span>
                  <p className="text-xs font-mono text-gray-700 mt-0.5">
                    &ldquo;{String(candidate.raw_value)}&rdquo;
                  </p>
                </div>
              )}
              <div>
                <span className="text-xs text-gray-500">Source Document:</span>
                <p className="text-xs font-mono text-blue-600 mt-0.5">
                  <Link
                    href={`/documents/${encodeURIComponent(item.document_id)}`}
                    className="hover:underline"
                  >
                    {item.document_id} &rarr;
                  </Link>
                </p>
              </div>
            </div>

            {/* Current Approved / Corrected State */}
            <div className="rounded-2xl border border-blue-100 bg-blue-50/40 p-6 shadow-xs space-y-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-blue-700">
                Current Approved / Corrected State
              </span>
              <div>
                <span className="text-xs text-gray-500">Effective Value:</span>
                <p className="text-base font-semibold text-blue-900 font-mono mt-0.5">
                  {item.current_revision
                    ? String(item.current_revision.corrected_value)
                    : String(candidate.value ?? "Pending Review")}
                </p>
              </div>
              {item.current_revision && (
                <>
                  <div>
                    <span className="text-xs text-gray-500">Correction Rationale:</span>
                    <p className="text-xs text-gray-800 mt-0.5 italic">
                      &ldquo;{item.current_revision.rationale}&rdquo;
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Verified Evidence Quote:</span>
                    <p className="text-xs font-mono text-gray-800 mt-0.5 bg-white p-2.5 rounded border border-blue-200">
                      &ldquo;{item.current_revision.evidence_quote || "None"}&rdquo;
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Quick Decision Form if in review */}
          <DecisionPanel
            item={item}
            onSubmitDecision={submitDecision}
            onClaim={claim}
            onReopen={reopen}
            submitting={submitting}
          />
        </div>
      )}

      {/* Tab Content: Fact Verification */}
      {activeTab === "verification" && (
        <FactVerificationPanel
          item={item}
          onRecordVerification={handleRecordVerification}
          disabled={submitting}
        />
      )}

      {/* Tab Content: Conflict Resolution */}
      {activeTab === "conflicts" && isConflict && (
        <ConflictResolutionPanel
          item={item}
          onResolveConflict={handleResolveConflict}
          disabled={submitting}
        />
      )}

      {/* Tab Content: Decision Management */}
      {activeTab === "decisions" && (
        <DecisionPanel
          item={item}
          onSubmitDecision={submitDecision}
          onClaim={claim}
          onReopen={reopen}
          submitting={submitting}
        />
      )}

      {/* Tab Content: Audit History */}
      {activeTab === "audit" && <AuditTimeline events={history} />}

      {/* Tab Content: Quality Feedback */}
      {activeTab === "feedback" && (
        <QualityFeedbackForm
          onSubmitFeedback={(fb) => sendFeedback(fb.category, fb.notes || "")}
          submitting={submitting}
        />
      )}
    </div>
  );
}

export default function ReviewDetailPage(props: PageProps) {
  return (
    <React.Suspense fallback={<div className="p-8 text-center text-gray-500">Loading review details...</div>}>
      <ReviewDetailContent {...props} />
    </React.Suspense>
  );
}
