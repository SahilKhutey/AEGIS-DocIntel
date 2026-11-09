import React, { useState } from "react";
import type { ReviewItem, DecisionType } from "../types";
import { isTerminalStatus } from "../utils/decision-transitions";
import type { DecisionSubmission } from "../types";

interface DecisionPanelProps {
  item: ReviewItem;
  onSubmitDecision: (submission: DecisionSubmission) => Promise<void>;
  onClaim?: () => Promise<void>;
  onReopen?: (rationale: string) => Promise<void>;
  submitting?: boolean;
}

export function DecisionPanel({
  item,
  onSubmitDecision,
  onClaim,
  onReopen,
  submitting = false,
}: DecisionPanelProps) {
  const isTerminal = isTerminalStatus(item.status);
  const canClaim = item.status === "pending" || item.status === "needs_evidence";
  const isInReview = item.status === "in_review";

  const [action, setAction] = useState<DecisionType>("approve");
  const [rationale, setRationale] = useState("");
  const [correctedValue, setCorrectedValue] = useState("");
  const [correctedType, setCorrectedType] = useState("string");
  const [unit, setUnit] = useState("");
  const [evidenceQuote, setEvidenceQuote] = useState("");
  const [confirmed, setConfirmed] = useState(false);

  // Administrative reopen state
  const [isReopening, setIsReopening] = useState(false);
  const [reopenRationale, setReopenRationale] = useState("");

  async function handleDecisionSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!rationale.trim() || rationale.trim().length < 3) return;
    if (action === "correct" && !correctedValue.trim()) return;

    let parsedValue: string | number | boolean = correctedValue;
    if (correctedType === "decimal" || correctedType === "integer") {
      const num = Number(correctedValue);
      if (!isNaN(num)) parsedValue = num;
    } else if (correctedType === "boolean") {
      parsedValue = correctedValue.toLowerCase() === "true";
    }

    await onSubmitDecision({
      action,
      expected_version: item.version,
      rationale: rationale.trim(),
      corrected_value: action === "correct" ? parsedValue : undefined,
      corrected_type: action === "correct" ? correctedType : undefined,
      unit: action === "correct" && unit ? unit : undefined,
      evidence_quote: action === "correct" && evidenceQuote ? evidenceQuote : undefined,
    });

    setRationale("");
    setCorrectedValue("");
    setEvidenceQuote("");
    setConfirmed(false);
  }

  async function handleReopenSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!reopenRationale.trim() || reopenRationale.trim().length < 5 || !onReopen) return;
    await onReopen(reopenRationale.trim());
    setIsReopening(false);
    setReopenRationale("");
  }

  return (
    <div
      className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs space-y-6"
      data-testid="decision-panel"
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-gray-100">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Governance Decision Management</h2>
          <p className="text-xs text-gray-500 mt-1">
            Enforce authoritative sign-off, corrections, and tamper-evident decision logging.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-gray-600 bg-gray-100 px-2.5 py-1 rounded-md">
            Version: v{item.version}
          </span>
          {canClaim && onClaim && (
            <button
              type="button"
              onClick={onClaim}
              disabled={submitting}
              className="rounded-lg bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-blue-500 disabled:opacity-50"
            >
              {submitting ? "Claiming..." : "Claim Item for Review"}
            </button>
          )}
          {isTerminal && onReopen && !isReopening && (
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
      {isReopening && onReopen && (
        <form
          onSubmit={handleReopenSubmit}
          className="rounded-xl bg-amber-50/60 border border-amber-200 p-4 space-y-3"
        >
          <h3 className="text-sm font-semibold text-amber-900">
            Administrative Reopen Justification
          </h3>
          <p className="text-xs text-amber-700">
            Reopening a terminal governance decision requires administrative authority and an audited rationale.
          </p>
          <textarea
            rows={2}
            required
            placeholder="State the compliance or legal rationale for reopening this item (min 5 characters)..."
            value={reopenRationale}
            onChange={(e) => setReopenRationale(e.target.value)}
            className="w-full rounded-lg border border-amber-300 p-2.5 text-xs text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-amber-500 bg-white"
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
              {submitting ? "Reopening..." : "Confirm Administrative Reopen"}
            </button>
          </div>
        </form>
      )}

      {/* Notice if item is not in review */}
      {!isInReview && !isTerminal && (
        <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-4 text-xs text-blue-800">
          This item is currently in <strong className="uppercase">{item.status}</strong> state.
          Claim this item before submitting a governance decision.
        </div>
      )}

      {isTerminal && (
        <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-xs text-gray-700">
          This item reached a terminal governance state (<strong className="uppercase">{item.status}</strong>).
          Review decisions are locked unless an administrator initiates an audited reopen.
        </div>
      )}

      {/* Decision Submission Form when item is in_review */}
      {isInReview && (
        <form onSubmit={handleDecisionSubmit} className="space-y-5">
          {/* Action Selector */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-600 mb-2">
              Select Governance Action <span className="text-rose-500">*</span>
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                {
                  act: "approve",
                  label: "Approve",
                  desc: "Affirm extraction matches evidence",
                  color: "hover:border-emerald-500 hover:bg-emerald-50/50",
                },
                {
                  act: "correct",
                  label: "Correct",
                  desc: "Update value with source citation",
                  color: "hover:border-purple-500 hover:bg-purple-50/50",
                },
                {
                  act: "reject",
                  label: "Reject",
                  desc: "Discard inaccurate or hallucinated statement",
                  color: "hover:border-rose-500 hover:bg-rose-50/50",
                },
                {
                  act: "request_evidence",
                  label: "Request Evidence",
                  desc: "Flag missing source context",
                  color: "hover:border-orange-500 hover:bg-orange-50/50",
                },
              ].map((opt) => {
                const isSelected = action === opt.act;
                return (
                  <button
                    key={opt.act}
                    type="button"
                    onClick={() => setAction(opt.act as DecisionType)}
                    className={`rounded-xl border p-3 text-left transition ${
                      isSelected
                        ? "border-blue-600 bg-blue-50 text-blue-700 shadow-xs ring-1 ring-blue-600"
                        : `border-gray-200 bg-white text-gray-700 ${opt.color}`
                    }`}
                  >
                    <p className="text-xs font-bold capitalize">{opt.label}</p>
                    <p className="text-[11px] text-gray-500 mt-0.5 leading-tight">{opt.desc}</p>
                  </button>
                );
              })}
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
                  placeholder="Exact quote from source document supporting this correction..."
                  value={evidenceQuote}
                  onChange={(e) => setEvidenceQuote(e.target.value)}
                  className="w-full rounded-lg border border-purple-300 p-2 text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-purple-500 bg-white"
                />
              </div>
            </div>
          )}

          {/* Rationale Input */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-600 mb-1">
              Reviewer Rationale <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={3}
              required
              minLength={3}
              placeholder="Explain the reason for this decision (required for tamper-evident audit history)..."
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              className="w-full rounded-xl border border-gray-300 p-3 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
            />
          </div>

          {/* Human oversight confirmation checkbox */}
          <div className="flex items-start gap-2 pt-1">
            <input
              id="confirm-decision"
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="confirm-decision" className="text-xs text-gray-600 select-none">
              I certify that I have verified the evidence citations and that this decision complies with governance policies.
            </label>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={
                submitting ||
                !confirmed ||
                !rationale.trim() ||
                (action === "correct" && !correctedValue.trim())
              }
              className="inline-flex items-center rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-semibold text-white shadow-xs hover:bg-blue-500 disabled:opacity-50"
            >
              {submitting ? "Committing Decision..." : `Submit ${action.toUpperCase()} &rarr;`}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
