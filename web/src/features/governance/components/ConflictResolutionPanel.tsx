import React, { useState } from "react";
import Link from "next/link";
import type { ReviewItem, ConflictResolutionOutcome } from "../types";
import { CONFLICT_RESOLUTION_CONFIG } from "../utils/conflict-utils";
import type { ConflictResolutionInput } from "../schemas/conflict.schema";

interface ConflictResolutionPanelProps {
  item: ReviewItem;
  onResolveConflict?: (input: ConflictResolutionInput) => Promise<void>;
  disabled?: boolean;
}

export function ConflictResolutionPanel({
  item,
  onResolveConflict,
  disabled = false,
}: ConflictResolutionPanelProps) {
  const candidate = (item.candidate_data || {}) as Record<string, unknown>;
  const subject = String(candidate.subject || "Contradiction Investigation");
  const attribute = String(candidate.attribute || item.candidate_id || "Cross-Document Discrepancy");

  // Support both structured conflict payloads and fallback representations
  const fact1 = (candidate.fact_1 || candidate.claim_a || {}) as Record<string, unknown>;
  const fact2 = (candidate.fact_2 || candidate.claim_b || {}) as Record<string, unknown>;

  const fact1Doc = String(fact1.document_id || item.document_id || "Document A");
  const fact1Val = String(fact1.value ?? candidate.value ?? "—");
  const fact1Quote = String(fact1.evidence_quote || candidate.raw_value || "");

  const fact2Doc = String(fact2.document_id || "Document B");
  const fact2Val = String(fact2.value ?? "—");
  const fact2Quote = String(fact2.evidence_quote || "");

  const [outcome, setOutcome] = useState<ConflictResolutionOutcome>("accepted_first_fact");
  const [rationale, setRationale] = useState("");
  const [reconciledValue, setReconciledValue] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [resolvedSuccess, setResolvedSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!rationale.trim() || rationale.trim().length < 5) return;

    if (onResolveConflict) {
      try {
        setIsSubmitting(true);
        await onResolveConflict({
          outcome,
          rationale: rationale.trim(),
          reconciled_value:
            outcome === "accepted_second_fact"
              ? fact2Val
              : outcome === "both_valid"
                ? reconciledValue || undefined
                : undefined,
          reconciled_evidence_quote:
            outcome === "accepted_first_fact"
              ? fact1Quote
              : outcome === "accepted_second_fact"
                ? fact2Quote
                : undefined,
        });
        setResolvedSuccess(true);
      } finally {
        setIsSubmitting(false);
      }
    }
  }

  return (
    <div
      className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs space-y-6"
      data-testid="conflict-resolution-panel"
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-gray-100">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded bg-purple-100 text-purple-800 text-[10px] font-mono px-2 py-0.5 uppercase font-semibold">
              Conflict Investigation
            </span>
            <h2 className="text-lg font-bold text-gray-900">
              {subject} &bull; {attribute}
            </h2>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Compare contradictory assertions across documents, evaluate provenance, and record resolution.
          </p>
        </div>
      </div>

      {/* Side-by-side comparison cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Claim A / Fact 1 */}
        <div className="rounded-xl border border-blue-200 bg-blue-50/20 p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-800">
              Claim 1 (Source A)
            </span>
            <span className="text-xs font-mono text-blue-600 truncate max-w-[150px]">
              {fact1Doc}
            </span>
          </div>
          <div>
            <span className="text-xs text-gray-500">Asserted Value:</span>
            <p className="text-base font-mono font-bold text-gray-900 bg-white p-2.5 rounded border border-blue-100 mt-0.5">
              {fact1Val}
            </p>
          </div>
          <div>
            <span className="text-xs text-gray-500">Source Evidence Passage:</span>
            <div className="bg-white p-3 rounded border border-blue-100 mt-0.5 min-h-[60px]">
              <p className="text-xs italic text-gray-700">
                {fact1Quote ? `“${fact1Quote}”` : "No direct quote available"}
              </p>
            </div>
          </div>
          <div className="pt-2 flex justify-end text-xs">
            <Link
              href={`/documents/${encodeURIComponent(fact1Doc)}`}
              className="text-blue-600 hover:underline font-medium"
            >
              Inspect Source A &rarr;
            </Link>
          </div>
        </div>

        {/* Claim B / Fact 2 */}
        <div className="rounded-xl border border-indigo-200 bg-indigo-50/20 p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-800">
              Claim 2 (Source B)
            </span>
            <span className="text-xs font-mono text-indigo-600 truncate max-w-[150px]">
              {fact2Doc}
            </span>
          </div>
          <div>
            <span className="text-xs text-gray-500">Asserted Value:</span>
            <p className="text-base font-mono font-bold text-gray-900 bg-white p-2.5 rounded border border-indigo-100 mt-0.5">
              {fact2Val}
            </p>
          </div>
          <div>
            <span className="text-xs text-gray-500">Source Evidence Passage:</span>
            <div className="bg-white p-3 rounded border border-indigo-100 mt-0.5 min-h-[60px]">
              <p className="text-xs italic text-gray-700">
                {fact2Quote ? `“${fact2Quote}”` : "No direct quote available"}
              </p>
            </div>
          </div>
          <div className="pt-2 flex justify-end text-xs">
            <Link
              href={`/documents/${encodeURIComponent(fact2Doc)}`}
              className="text-indigo-600 hover:underline font-medium"
            >
              Inspect Source B &rarr;
            </Link>
          </div>
        </div>
      </div>

      {/* Resolution options form */}
      <form onSubmit={handleSubmit} className="space-y-4 pt-2">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-2">
            Conflict Resolution Outcome
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {(
              [
                "accepted_first_fact",
                "accepted_second_fact",
                "both_valid",
                "insufficient_evidence",
                "escalated",
              ] as ConflictResolutionOutcome[]
            ).map((out) => {
              const conf = CONFLICT_RESOLUTION_CONFIG[out];
              const isSelected = outcome === out;
              return (
                <button
                  key={out}
                  type="button"
                  disabled={disabled}
                  onClick={() => setOutcome(out)}
                  className={`rounded-xl border p-3 text-left transition ${
                    isSelected
                      ? `ring-2 ring-purple-600 bg-purple-50/50 border-purple-300`
                      : "border-gray-200 bg-white hover:bg-gray-50"
                  } disabled:opacity-50`}
                >
                  <p className={`text-xs font-bold ${conf.badgeText}`}>{conf.label}</p>
                  <p className="text-[11px] text-gray-500 mt-1 leading-snug">
                    {conf.description}
                  </p>
                </button>
              );
            })}
          </div>
        </div>

        {/* If reconciled / both valid, prompt for qualified value */}
        {outcome === "both_valid" && (
          <div className="rounded-xl border border-purple-200 bg-purple-50/40 p-4 space-y-2">
            <label className="block text-xs font-medium text-purple-900">
              Reconciled Value or Scope Qualification <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={reconciledValue}
              onChange={(e) => setReconciledValue(e.target.value)}
              placeholder="e.g. Q3: $142.5M (pre-audit), Annualized: $148.0M"
              className="w-full rounded-lg border border-purple-300 p-2 text-sm text-gray-900 bg-white focus:outline-none focus:ring-1 focus:ring-purple-500"
            />
          </div>
        )}

        {/* Resolution rationale */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1">
            Resolution Rationale <span className="text-rose-500">*</span>
          </label>
          <textarea
            rows={2}
            required
            minLength={5}
            disabled={disabled}
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            placeholder="Document the governance rationale for this cross-document resolution (min 5 chars)..."
            className="w-full rounded-xl border border-gray-300 p-3 text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {resolvedSuccess && (
          <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-xs text-emerald-800">
            Conflict resolution recorded successfully!
          </div>
        )}

        {onResolveConflict && (
          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={disabled || isSubmitting || rationale.trim().length < 5}
              className="rounded-xl bg-purple-600 px-5 py-2.5 text-xs font-semibold text-white shadow-xs hover:bg-purple-500 disabled:opacity-50"
            >
              {isSubmitting ? "Committing Resolution..." : "Commit Conflict Resolution &rarr;"}
            </button>
          </div>
        )}
      </form>
    </div>
  );
}
