"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  DocumentListSchema,
  AnswerSchema,
  type DocumentItem,
  type AnswerResult,
  type Evidence,
} from "@/lib/schemas";
import { apiRequest } from "@/lib/api-client";
import { ApiError } from "@/lib/errors";
import { EvidencePanel } from "@/components/evidence-panel";
import { ErrorState } from "@/components/error-state";

function AskContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialDocId = searchParams.get("doc_id") || "";

  const [question, setQuestion] = useState("");
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>(
    initialDocId ? [initialDocId] : [],
  );
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [answerResult, setAnswerResult] = useState<AnswerResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [docsLoading, setDocsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeCitationIndex, setActiveCitationIndex] = useState<number | null>(null);

  useEffect(() => {
    async function loadDocs() {
      try {
        setDocsLoading(true);
        const data = await apiRequest("/api/v1/documents", DocumentListSchema);
        setDocuments(data.items || []);
      } catch {
        // Continue even if document list fails to load
      } finally {
        setDocsLoading(false);
      }
    }
    loadDocs();
  }, []);

  async function handleAsk(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!question.trim()) return;

    try {
      setLoading(true);
      setError(null);
      setActiveCitationIndex(null);

      const payload = {
        question: question.trim(),
        document_ids: selectedDocIds.length > 0 ? selectedDocIds : [],
      };

      const result = await apiRequest("/api/v1/ask", AnswerSchema, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setAnswerResult(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to obtain grounded answer.");
    } finally {
      setLoading(false);
    }
  }

  // Synthesize evidence items from citations + evidence array
  const displayEvidence: Evidence[] = (answerResult?.evidence && answerResult.evidence.length > 0)
    ? answerResult.evidence
    : (answerResult?.citations || []).map((c, i) => ({
        document_id: c.document_id,
        chunk_id: c.evidence_id,
        quote: answerResult?.warnings?.[i] || "Cited source passage",
        page_number: c.page_number,
        section_path: c.section_path,
      }));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Ask &amp; Evidence Explorer
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Ask questions across authorized documents with strictly grounded citations and transparent abstention.
        </p>
      </div>

      {/* Query Form */}
      <form onSubmit={handleAsk} className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs space-y-4">
        <div>
          <label htmlFor="question-input" className="block text-sm font-semibold text-gray-900 mb-1">
            Your Question
          </label>
          <textarea
            id="question-input"
            rows={3}
            placeholder="e.g., What is the aggregate liability cap under the agreement, and what exceptions apply?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="w-full rounded-xl border border-gray-300 p-3 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            required
          />
        </div>

        {/* Document Scope Filter */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
            Document Scope (optional filter)
          </label>
          {docsLoading ? (
            <p className="text-xs text-gray-400">Loading authorized documents...</p>
          ) : documents.length === 0 ? (
            <p className="text-xs text-gray-500">Searching all tenant documents.</p>
          ) : (
            <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-1">
              {documents.map((d) => {
                const isSelected = selectedDocIds.includes(d.doc_id);
                return (
                  <button
                    key={d.doc_id}
                    type="button"
                    onClick={() => {
                      setSelectedDocIds((prev) =>
                        isSelected ? prev.filter((id) => id !== d.doc_id) : [...prev, d.doc_id],
                      );
                    }}
                    className={`rounded-lg px-2.5 py-1 text-xs font-medium border transition ${
                      isSelected
                        ? "bg-blue-600 text-white border-blue-600"
                        : "bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100"
                    }`}
                  >
                    {d.filename} {isSelected ? "✓" : ""}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="inline-flex items-center rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-blue-500 disabled:opacity-50"
          >
            {loading ? "Grounding & Generating..." : "Ask Question &rarr;"}
          </button>
        </div>
      </form>

      {error && (
        <ErrorState
          title="Query Error"
          message={error}
          onRetry={() => { void handleAsk(); }}
        />
      )}

      {/* Answer & Evidence Display */}
      {answerResult && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Main Answer Column */}
          <div className="lg:col-span-2 space-y-4">
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs">
              <div className="flex items-center justify-between pb-3 border-b border-gray-100 mb-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                  Grounded Answer
                </span>
                {answerResult.insufficient_evidence ? (
                  <span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800">
                    Safe Abstention: Insufficient Evidence
                  </span>
                ) : (
                  <span className="inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800">
                    Verified Grounded
                  </span>
                )}
              </div>

              <div className="text-gray-900 leading-relaxed whitespace-pre-wrap text-base">
                {answerResult.answer}
              </div>

              {/* Citations List in Answer */}
              {answerResult.citations.length > 0 && (
                <div className="mt-6 pt-4 border-t border-gray-100">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                    Citations ({answerResult.citations.length})
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {answerResult.citations.map((cite, idx) => (
                      <button
                        key={`${cite.document_id}-${idx}`}
                        type="button"
                        onClick={() => setActiveCitationIndex(idx)}
                        className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium border transition ${
                          activeCitationIndex === idx
                            ? "bg-blue-100 text-blue-900 border-blue-400 font-semibold"
                            : "bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100"
                        }`}
                      >
                        <span>[{idx + 1}]</span>
                        <span className="truncate max-w-[120px]">{cite.document_id}</span>
                        {cite.page_number && <span className="text-gray-400">p.{cite.page_number}</span>}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Warnings / Conflicting Sources */}
              {answerResult.warnings.length > 0 && (
                <div className="mt-4 rounded-lg bg-amber-50 border border-amber-200 p-3 text-xs text-amber-900">
                  <div className="font-semibold mb-1">Source Inconsistency Warnings:</div>
                  <ul className="list-disc pl-4 space-y-0.5">
                    {answerResult.warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Evidence Panel Column */}
          <div className="lg:col-span-1">
            <EvidencePanel
              evidence={displayEvidence}
              onOpenSource={(item) => {
                router.push(`/documents/${encodeURIComponent(item.document_id)}`);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default function AskPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gray-500">Loading Ask Workbench...</div>}>
      <AskContent />
    </Suspense>
  );
}
