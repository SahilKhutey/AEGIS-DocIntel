import React, { useState } from "react";
import Link from "next/link";
import type { ReviewItem, FactVerificationStatus } from "../types";
import {
  VERIFICATION_CONFIG,
  mapVerificationToDecision,
} from "../utils/verification-utils";
import type { FactVerificationInput } from "../schemas/verification.schema";

interface FactVerificationPanelProps {
  item: ReviewItem;
  onRecordVerification?: (
    input: FactVerificationInput,
    correctedValue?: string,
  ) => Promise<void>;
  disabled?: boolean;
}

export function FactVerificationPanel({
  item,
  onRecordVerification,
  disabled = false,
}: FactVerificationPanelProps) {
  const candidate = item.candidate_data || {};
  const subject = String(candidate.subject || "Candidate Fact");
  const attribute = String(candidate.attribute || item.candidate_id || "Field");
  const extractedValue = String(
    candidate.value ?? candidate.raw_value ?? item.extracted_value ?? "—",
  );
  const rawSource = candidate.raw_value ? String(candidate.raw_value) : null;
  const quote = String(candidate.evidence_quote || candidate.quote || "");
  const pageNum = candidate.page_number ?? item.page_number;
  const confidence =
    typeof candidate.confidence === "number"
      ? candidate.confidence
      : typeof item.confidence === "number"
        ? item.confidence
        : null;

  const [verificationStatus, setVerificationStatus] =
    useState<FactVerificationStatus>("verified");
  const [rationale, setRationale] = useState("");
  const [correctedValue, setCorrectedValue] = useState("");
  const [verifiedQuote, setVerifiedQuote] = useState(quote);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionSuccess, setSubmissionSuccess] = useState(false);

  const recommendedDecision = mapVerificationToDecision(verificationStatus);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!rationale.trim() || rationale.trim().length < 3) return;

    if (onRecordVerification) {
      try {
        setIsSubmitting(true);
        await onRecordVerification(
          {
            verification_status: verificationStatus,
            rationale: rationale.trim(),
            verified_quote: verifiedQuote || undefined,
          },
          verificationStatus === "partially_verified" ? correctedValue : undefined,
        );
        setSubmissionSuccess(true);
      } finally {
        setIsSubmitting(false);
      }
    }
  }

  return (
    <div
      className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs space-y-6"
      data-testid="fact-verification-panel"
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-gray-100">
        <div>
          <h2 className="text-lg font-bold text-gray-900">
            Fact Verification: {subject} &bull; {attribute}
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            Compare extracted statement against source citations and record an evidence-grounded verification.
          </p>
        </div>
        {confidence !== null && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Extraction Confidence:</span>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-mono font-semibold ${
                confidence >= 0.9
                  ? "bg-emerald-100 text-emerald-800"
                  : confidence >= 0.7
                    ? "bg-amber-100 text-amber-800"
                    : "bg-rose-100 text-rose-800"
              }`}
            >
              {(confidence * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>

      {/* Grid: Extracted statement vs Source Passage */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Extracted statement */}
        <div className="rounded-xl border border-gray-100 bg-gray-50/75 p-5 space-y-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
            Extracted Statement &amp; Metadata
          </span>
          <div>
            <span className="text-xs text-gray-500">Subject:</span>
            <p className="text-sm font-semibold text-gray-900">{subject}</p>
          </div>
          <div>
            <span className="text-xs text-gray-500">Attribute:</span>
            <p className="text-sm font-mono text-gray-800">{attribute}</p>
          </div>
          <div>
            <span className="text-xs text-gray-500">Inferred Value:</span>
            <p className="text-base font-mono font-bold text-blue-700 bg-white p-2.5 rounded border border-gray-200 mt-0.5">
              {extractedValue}
            </p>
          </div>
          {rawSource && (
            <div>
              <span className="text-xs text-gray-500">Raw Extracted String:</span>
              <p className="text-xs font-mono text-gray-700 mt-0.5">&ldquo;{rawSource}&rdquo;</p>
            </div>
          )}
          <div className="pt-2 border-t border-gray-200/60 flex items-center justify-between text-xs text-gray-500">
            <span>Doc ID: {item.document_id}</span>
            {pageNum !== undefined && pageNum !== null && <span>Page: {String(pageNum)}</span>}
            <Link
              href={`/documents/${encodeURIComponent(item.document_id)}`}
              className="text-blue-600 hover:underline font-medium"
            >
              Open Document &rarr;
            </Link>
          </div>
        </div>

        {/* Right: Cited Evidence Passage */}
        <div className="rounded-xl border border-blue-100 bg-blue-50/30 p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-700">
              Cited Evidence Passage
            </span>
            <span className="text-[10px] font-mono bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
              Grounded Citation
            </span>
          </div>

          <div className="bg-white p-3 rounded-lg border border-blue-200 min-h-[100px]">
            {quote ? (
              <blockquote className="text-xs text-gray-800 italic leading-relaxed">
                &ldquo;{quote}&rdquo;
              </blockquote>
            ) : (
              <p className="text-xs text-gray-400 italic">
                No explicit text quote was bound during candidate fact extraction.
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Authoritative Source Excerpt (for verification audit)
            </label>
            <textarea
              rows={2}
              value={verifiedQuote}
              onChange={(e) => setVerifiedQuote(e.target.value)}
              placeholder="Paste exact verifying excerpt from source document..."
              className="w-full rounded-lg border border-gray-300 p-2 text-xs text-gray-900 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Verification Outcomes Selector */}
      <form onSubmit={handleSubmit} className="space-y-4 pt-2">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-2">
            Verification Outcome
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
            {(
              [
                "verified",
                "partially_verified",
                "not_verified",
                "contradicted",
                "insufficient_evidence",
              ] as FactVerificationStatus[]
            ).map((st) => {
              const conf = VERIFICATION_CONFIG[st];
              const isSelected = verificationStatus === st;
              return (
                <button
                  key={st}
                  type="button"
                  disabled={disabled}
                  onClick={() => setVerificationStatus(st)}
                  className={`rounded-xl border p-3 text-left transition ${
                    isSelected
                      ? `ring-2 ring-blue-600 ${conf.badgeBg} ${conf.border}`
                      : "border-gray-200 bg-white hover:bg-gray-50"
                  } disabled:opacity-50`}
                >
                  <p className={`text-xs font-bold ${conf.badgeText}`}>{conf.label}</p>
                  <p className="text-[11px] text-gray-500 mt-1 line-clamp-2 leading-tight">
                    {conf.description}
                  </p>
                </button>
              );
            })}
          </div>
        </div>

        {/* If partially verified, prompt for corrected value */}
        {verificationStatus === "partially_verified" && (
          <div className="rounded-xl border border-purple-200 bg-purple-50/40 p-4 space-y-2">
            <label className="block text-xs font-medium text-purple-900">
              Human-Corrected Value <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={correctedValue}
              onChange={(e) => setCorrectedValue(e.target.value)}
              placeholder="Provide corrected value based on source evidence..."
              className="w-full rounded-lg border border-purple-300 p-2 text-sm text-gray-900 bg-white focus:outline-none focus:ring-1 focus:ring-purple-500"
            />
          </div>
        )}

        {/* Reviewer Rationale */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-gray-700 mb-1">
            Verification Rationale <span className="text-rose-500">*</span>
          </label>
          <textarea
            rows={2}
            required
            minLength={3}
            disabled={disabled}
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            placeholder="Explain why this verification outcome was reached..."
            className="w-full rounded-xl border border-gray-300 p-3 text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {submissionSuccess && (
          <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-xs text-emerald-800">
            Verification recorded successfully! Recommended decision action: &ldquo;
            <span className="font-bold uppercase">{recommendedDecision}</span>&rdquo;.
          </div>
        )}

        {onRecordVerification && (
          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-gray-500">
              Recommended formal action:{" "}
              <span className="font-semibold text-gray-900 uppercase">
                {recommendedDecision}
              </span>
            </span>
            <button
              type="submit"
              disabled={disabled || isSubmitting || rationale.trim().length < 3}
              className="rounded-xl bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-blue-500 disabled:opacity-50"
            >
              {isSubmitting ? "Recording Verification..." : "Record Verification & Proceed"}
            </button>
          </div>
        )}
      </form>
    </div>
  );
}
