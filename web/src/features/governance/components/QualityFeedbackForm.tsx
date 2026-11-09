import React, { useState } from "react";
import type { FeedbackInput } from "../schemas/decision.schema";

interface QualityFeedbackFormProps {
  onSubmitFeedback: (feedback: FeedbackInput) => Promise<void>;
  submitting?: boolean;
}

export function QualityFeedbackForm({
  onSubmitFeedback,
  submitting = false,
}: QualityFeedbackFormProps) {
  const [category, setCategory] = useState<FeedbackInput["category"]>("wrong_value");
  const [notes, setNotes] = useState("");
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await onSubmitFeedback({
      category,
      notes: notes.trim(),
    });
    setSuccess(true);
    setNotes("");
  }

  return (
    <div
      className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs space-y-4"
      data-testid="quality-feedback-form"
    >
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-gray-900">
            Evaluation Feedback &amp; Continuous Learning Loop
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Record structured diagnostic feedback to improve automated extraction fidelity and benchmark evaluations.
          </p>
        </div>
      </div>

      {success ? (
        <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3 text-xs text-emerald-800">
          Diagnostic feedback recorded for evaluation datasets and fine-tuning benchmarks.
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Issue Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as FeedbackInput["category"])}
                className="w-full rounded-lg border border-gray-300 p-2 text-xs text-gray-900 bg-white"
              >
                <option value="wrong_value">Wrong Value</option>
                <option value="wrong_attribute">Wrong Attribute</option>
                <option value="bad_evidence">Bad Evidence Passage</option>
                <option value="hallucination">Hallucination</option>
                <option value="missing_context">Missing Context</option>
                <option value="other">Other Diagnostic Issue</option>
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Diagnostic Notes
              </label>
              <input
                type="text"
                placeholder="e.g., Extracted value was missing the amendment clause on page 14..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full rounded-lg border border-gray-300 p-2 text-xs text-gray-900 bg-white"
              />
            </div>
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-gray-800 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-gray-700 disabled:opacity-50"
            >
              {submitting ? "Recording..." : "Record Feedback"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
