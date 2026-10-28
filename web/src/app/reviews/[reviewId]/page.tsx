"use client";

import React, { useState, useEffect, use, useRef } from "react";
import Link from "next/link";
import {
  ReviewItemSchema,
  AuditEventSchema,
  type ReviewItem,
  type AuditEvent,
} from "@/lib/schemas";
import { apiRequest } from "@/lib/api-client";
import { ApiError } from "@/lib/errors";
import {
  submitReviewDecision,
  claimReviewItem,
  reopenReviewItem,
  type ReviewAction,
} from "@/features/reviews/submit-decision";
import { StatusBadge } from "@/components/status-badge";
import { ErrorState } from "@/components/error-state";
import { z } from "zod";

interface PageProps {
  params: Promise<{ reviewId: string }>;
}

function ReviewDetailContent({ params }: PageProps) {
  const { reviewId } = use(params);

  const [item, setItem] = useState<ReviewItem | null>(null);
  const [history, setHistory] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [staleWarning, setStaleWarning] = useState(false);

  // Decision Form State
  const [action, setAction] = useState<ReviewAction>("approve");
  const [rationale, setRationale] = useState("");
  const [correctedValue, setCorrectedValue] = useState("");
  const [correctedType, setCorrectedType] = useState("string");
  const [unit, setUnit] = useState("");
  const [evidenceQuote, setEvidenceQuote] = useState("");
  const idempotencyKeyRef = useRef<string>(`idem-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`);

  // Feedback State
  const [feedbackCategory, setFeedbackCategory] = useState("wrong_value");
  const [feedbackNotes, setFeedbackNotes] = useState("");
  const [feedbackSuccess, setFeedbackSuccess] = useState(false);

  // Administrative Reopen State
  const [reopenRationale, setReopenRationale] = useState("");
  const [isReopening, setIsReopening] = useState(false);

  async function loadReview() {
    try {
      setLoading(true);
      setError(null);
      setStaleWarning(false);
      const encodedId = encodeURIComponent(reviewId);

      // Fetch review item
      const itemData = await apiRequest(`/api/v1/reviews/${encodedId}`, ReviewItemSchema);
      setItem(itemData);

      // Fetch audit history
      try {
        const historyData = await apiRequest(
          `/api/v1/reviews/${encodedId}/history`,
          z.array(AuditEventSchema),
        );
        setHistory(historyData);
      } catch {
        // Audit history optional
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load review item.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReview();
  }, [reviewId]);

  async function handleClaim() {
    if (!item) return;
    try {
      setSubmitting(true);
      setError(null);
      const updated = await claimReviewItem(item.review_id, item.version);
      setItem(updated);
      setSuccessMessage("Item claimed successfully.");
      loadReview();
    } catch (err) {
      if (err instanceof ApiError && err.isConflict) {
        setStaleWarning(true);
      } else {
        setError(err instanceof ApiError ? err.message : "Failed to claim item.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSubmitDecision(e: React.FormEvent) {
    e.preventDefault();
    if (!item) return;

    if (!rationale.trim() || rationale.trim().length < 3) {
      setError("Rationale must be at least 3 characters.");
      return;
    }

    if (action === "correct" && !correctedValue.trim()) {
      setError("Please provide a corrected value.");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      setSuccessMessage(null);

      // Cast value if type specified
      let parsedValue: string | number | boolean = correctedValue;
      if (correctedType === "decimal" || correctedType === "integer") {
        const num = Number(correctedValue);
        if (!isNaN(num)) parsedValue = num;
      } else if (correctedType === "boolean") {
        parsedValue = correctedValue.toLowerCase() === "true";
      }

      const res = await submitReviewDecision(
        item.review_id,
        {
          action,
          expected_version: item.version,
          rationale: rationale.trim(),
          corrected_value: action === "correct" ? parsedValue : undefined,
          corrected_type: action === "correct" ? correctedType : undefined,
          unit: action === "correct" && unit ? unit : undefined,
          evidence_quote: action === "correct" && evidenceQuote ? evidenceQuote : undefined,
        },
        idempotencyKeyRef.current,
      );

      setItem(res.item);
      setSuccessMessage(`Decision '${action}' committed successfully.`);
      setRationale("");
      setCorrectedValue("");
      // Reset idempotency key for future operations
      idempotencyKeyRef.current = `idem-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      loadReview();
    } catch (err) {
      if (err instanceof ApiError && err.isConflict) {
        setStaleWarning(true);
      } else {
        setError(err instanceof ApiError ? err.message : "Failed to submit decision.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleFeedbackSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!item) return;

    try {
      setSubmitting(true);
      const encodedId = encodeURIComponent(item.review_id);
      await apiRequest(
        `/api/v1/reviews/${encodedId}/feedback`,
        z.object({ status: z.string() }),
        {
          method: "POST",
          body: JSON.stringify({
            category: feedbackCategory,
            notes: feedbackNotes,
          }),
        },
      );
      setFeedbackSuccess(true);
      setFeedbackNotes("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to record feedback.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleReopenSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!item) return;
    if (!reopenRationale.trim() || reopenRationale.trim().length < 5) {
      setError("Reopening justification must be at least 5 characters.");
      return;
    }

    try {
      setSubmitting(true);
      const res = await reopenReviewItem(item.review_id, item.version, reopenRationale);
      setItem(res.item);
      setIsReopening(false);
      setReopenRationale("");
      setSuccessMessage("Review reopened successfully.");
      loadReview();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Administrative reopen failed.");
    } finally {
      setSubmitting(false);
    }
  }

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
        <ErrorState title="Review Inaccessible" message={error} onRetry={loadReview} />
      </div>
    );
  }

  if (!item) return null;

  const candidate = item.candidate_data || {};
  const subjectStr = String(candidate.subject || "Fact");
  const attributeStr = String(candidate.attribute || item.candidate_id || item.review_id);
  const rawValueStr = candidate.raw_value ? String(candidate.raw_value) : null;
  const isTerminal = ["approved", "corrected", "rejected"].includes(item.status);
  const canClaim = item.status === "pending" || item.status === "needs_evidence";

  return (
    <div className="space-y-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/reviews" className="hover:text-blue-600">
          Review Queue
        </Link>
        <span>/</span>
        <span className="text-gray-900 font-medium truncate max-w-sm">
          {subjectStr} &bull; {attributeStr}
        </span>
      </div>

      {staleWarning && (
        <div role="alert" className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-amber-900">
          <div className="flex items-center justify-between">
            <div className="text-sm">
              <span className="font-bold">⚠️ Stale review version detected!</span> Another reviewer has modified this item. Please reload to inspect the latest state.
            </div>
            <button
              type="button"
              onClick={loadReview}
              className="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-700"
            >
              Reload Latest
            </button>
          </div>
        </div>
      )}

      {successMessage && (
        <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          {successMessage}
        </div>
      )}

      {error && <ErrorState title="Review Action Error" message={error} onRetry={loadReview} />}

      {/* Item Overview Card */}
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-gray-100">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
                {subjectStr} &bull; {attributeStr}
              </h1>
              <StatusBadge status={item.status} />
            </div>
            <p className="text-xs font-mono text-gray-400 mt-1">Review ID: {item.review_id}</p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2.5 py-1 rounded-md">
              Version: v{item.version}
            </span>
            {canClaim && (
              <button
                type="button"
                onClick={handleClaim}
                disabled={submitting}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-xs hover:bg-blue-500 disabled:opacity-50"
              >
                Claim Item
              </button>
            )}
            {isTerminal && !isReopening && (
              <button
                type="button"
                onClick={() => setIsReopening(true)}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50"
              >
                Administrative Reopen
              </button>
            )}
          </div>
        </div>

        {/* Administrative Reopen Form */}
        {isReopening && (
          <form onSubmit={handleReopenSubmit} className="rounded-xl bg-amber-50/60 border border-amber-200 p-4 space-y-3">
            <h3 className="text-sm font-semibold text-amber-900">Administrative Reopen Justification</h3>
            <textarea
              rows={2}
              required
              placeholder="State the compliance or legal rationale for reopening a terminal review..."
              value={reopenRationale}
              onChange={(e) => setReopenRationale(e.target.value)}
              className="w-full rounded-lg border border-amber-300 p-2.5 text-xs text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-amber-500"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setIsReopening(false)}
                className="rounded px-3 py-1 text-xs text-gray-600 hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting || reopenRationale.trim().length < 5}
                className="rounded bg-amber-600 px-3 py-1 text-xs font-semibold text-white hover:bg-amber-700 disabled:opacity-50"
              >
                Confirm Reopen
              </button>
            </div>
          </form>
        )}

        {/* Candidate & Revision Comparison */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Original Candidate State */}
          <div className="rounded-xl border border-gray-100 bg-gray-50/75 p-4 space-y-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
              Original System Inference
            </span>
            <div>
              <span className="text-xs text-gray-500">Extracted Value:</span>
              <p className="text-base font-semibold text-gray-900 font-mono mt-0.5">
                {String(candidate.value ?? candidate.raw_value ?? "—")}
              </p>
            </div>
            {rawValueStr && (
              <div>
                <span className="text-xs text-gray-500">Raw Source Text:</span>
                <p className="text-xs font-mono text-gray-700 mt-0.5">&ldquo;{rawValueStr}&rdquo;</p>
              </div>
            )}
            <div>
              <span className="text-xs text-gray-500">Source Document:</span>
              <p className="text-xs font-mono text-blue-600 mt-0.5">
                <Link href={`/documents/${encodeURIComponent(item.document_id)}`} className="hover:underline">
                  {item.document_id} &rarr;
                </Link>
              </p>
            </div>
          </div>

          {/* Current Decision / Revision State */}
          <div className="rounded-xl border border-blue-100 bg-blue-50/40 p-4 space-y-3">
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
                  <p className="text-xs font-mono text-gray-800 mt-0.5 bg-white p-2 rounded border border-blue-200">
                    &ldquo;{item.current_revision.evidence_quote || "None"}&rdquo;
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Decision Submission Form */}
      {!isTerminal && (
        <form
          onSubmit={handleSubmitDecision}
          className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs space-y-6"
        >
          <div className="pb-3 border-b border-gray-100">
            <h2 className="text-base font-semibold text-gray-900">Submit Review Decision</h2>
            <p className="text-xs text-gray-500 mt-1">
              Select an action and provide a rationale. Corrections require verified evidence grounding.
            </p>
          </div>

          {/* Action Selector */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
              Action
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { act: "approve", label: "Approve", color: "hover:border-emerald-500 hover:bg-emerald-50/50" },
                { act: "correct", label: "Correct", color: "hover:border-purple-500 hover:bg-purple-50/50" },
                { act: "reject", label: "Reject", color: "hover:border-rose-500 hover:bg-rose-50/50" },
                { act: "request_evidence", label: "Request Evidence", color: "hover:border-orange-500 hover:bg-orange-50/50" },
              ].map((opt) => (
                <button
                  key={opt.act}
                  type="button"
                  onClick={() => setAction(opt.act as ReviewAction)}
                  className={`rounded-xl border p-3 text-center text-sm font-semibold capitalize transition ${
                    action === opt.act
                      ? "border-blue-600 bg-blue-50 text-blue-700 shadow-xs ring-1 ring-blue-600"
                      : `border-gray-200 bg-white text-gray-700 ${opt.color}`
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Correction Specific Fields */}
          {action === "correct" && (
            <div className="rounded-xl bg-purple-50/40 border border-purple-200 p-4 space-y-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-purple-900">
                Correction Details
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <div className="sm:col-span-2">
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Corrected Value <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g., 2500000.0 or New Value"
                    value={correctedValue}
                    onChange={(e) => setCorrectedValue(e.target.value)}
                    className="w-full rounded-lg border border-purple-300 p-2 text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-purple-500 bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Type</label>
                  <select
                    value={correctedType}
                    onChange={(e) => setCorrectedType(e.target.value)}
                    className="w-full rounded-lg border border-purple-300 p-2 text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-purple-500 bg-white"
                  >
                    <option value="string">String</option>
                    <option value="decimal">Decimal</option>
                    <option value="integer">Integer</option>
                    <option value="boolean">Boolean</option>
                    <option value="date">Date</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Unit</label>
                  <input
                    type="text"
                    placeholder="e.g. USD"
                    value={unit}
                    onChange={(e) => setUnit(e.target.value)}
                    className="w-full rounded-lg border border-purple-300 p-2 text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-purple-500 bg-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Authoritative Evidence Quote (min 8 characters)
                </label>
                <input
                  type="text"
                  placeholder="Exact quote from source document..."
                  value={evidenceQuote}
                  onChange={(e) => setEvidenceQuote(e.target.value)}
                  className="w-full rounded-lg border border-purple-300 p-2 text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-purple-500 bg-white"
                />
              </div>
            </div>
          )}

          {/* Rationale Input */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1">
              Reviewer Rationale <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={3}
              required
              minLength={3}
              placeholder="Explain the reason for this decision (required for audit compliance)..."
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              className="w-full rounded-xl border border-gray-300 p-3 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={submitting || !rationale.trim()}
              className="inline-flex items-center rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-blue-500 disabled:opacity-50"
            >
              {submitting ? "Committing Decision..." : `Submit ${action.toUpperCase()} &rarr;`}
            </button>
          </div>
        </form>
      )}

      {/* Append-Only Audit Trail */}
      <div className="rounded-2xl border border-gray-200 bg-white shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">
            Append-Only Audit History ({history.length})
          </h2>
          <span className="text-xs font-mono text-gray-400">Tamper-evident trail</span>
        </div>
        {history.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-500 italic">
            No audit events recorded yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
              <thead className="bg-gray-50 text-xs font-semibold uppercase text-gray-500">
                <tr>
                  <th scope="col" className="px-6 py-3">Seq</th>
                  <th scope="col" className="px-6 py-3">Timestamp</th>
                  <th scope="col" className="px-6 py-3">Actor</th>
                  <th scope="col" className="px-6 py-3">Action</th>
                  <th scope="col" className="px-6 py-3">Status Transition</th>
                  <th scope="col" className="px-6 py-3">Version</th>
                  <th scope="col" className="px-6 py-3">Rationale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 font-mono text-xs">
                {history.map((ev) => (
                  <tr key={ev.event_id} className="hover:bg-gray-50">
                    <td className="px-6 py-3 font-bold text-gray-600">{ev.sequence}</td>
                    <td className="px-6 py-3 text-gray-500 whitespace-nowrap">
                      {new Date(ev.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-3 text-gray-900 font-medium">{ev.actor_id}</td>
                    <td className="px-6 py-3 font-semibold uppercase text-blue-700">{ev.action}</td>
                    <td className="px-6 py-3 whitespace-nowrap">
                      <span className="text-gray-500">{ev.previous_status}</span>
                      <span className="mx-1 text-gray-400">&rarr;</span>
                      <span className="font-semibold text-gray-900">{ev.new_status}</span>
                    </td>
                    <td className="px-6 py-3 text-gray-500">
                      v{ev.previous_version} &rarr; v{ev.new_version}
                    </td>
                    <td className="px-6 py-3 font-sans text-xs text-gray-700 max-w-sm truncate">
                      {ev.rationale}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Reviewer Feedback Form */}
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs space-y-4">
        <h2 className="text-base font-semibold text-gray-900">
          Evaluation Feedback &amp; Quality Loop
        </h2>
        <p className="text-xs text-gray-500">
          Record diagnostic feedback to improve automated extraction fidelity and benchmark evaluations.
        </p>

        {feedbackSuccess ? (
          <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3 text-xs text-emerald-800">
            Thank you! Feedback recorded for evaluation datasets.
          </div>
        ) : (
          <form onSubmit={handleFeedbackSubmit} className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Issue Category
                </label>
                <select
                  value={feedbackCategory}
                  onChange={(e) => setFeedbackCategory(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 p-2 text-xs text-gray-900 bg-white"
                >
                  <option value="wrong_value">Wrong Value</option>
                  <option value="wrong_attribute">Wrong Attribute</option>
                  <option value="bad_evidence">Bad Evidence Passage</option>
                  <option value="hallucination">Hallucination</option>
                  <option value="missing_context">Missing Context</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Diagnostic Notes
                </label>
                <input
                  type="text"
                  placeholder="e.g., Extracted value was missing the amendment clause on page 14..."
                  value={feedbackNotes}
                  onChange={(e) => setFeedbackNotes(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 p-2 text-xs text-gray-900"
                />
              </div>
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={submitting}
                className="rounded-lg bg-gray-800 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-gray-700 disabled:opacity-50"
              >
                Record Feedback
              </button>
            </div>
          </form>
        )}
      </div>
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
