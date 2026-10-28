"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  DocumentListSchema,
  DocumentComparisonSchema,
  type DocumentItem,
  type DocumentComparison,
} from "@/lib/schemas";
import { apiRequest } from "@/lib/api-client";
import { ApiError } from "@/lib/errors";
import { StatusBadge } from "@/components/status-badge";
import { ErrorState } from "@/components/error-state";
import { EmptyState } from "@/components/empty-state";

export default function ComparePage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<DocumentComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [docsLoading, setDocsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadInitialData() {
      try {
        setDocsLoading(true);
        const docsData = await apiRequest("/api/v1/documents", DocumentListSchema);
        setDocuments(docsData.items || []);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load documents.");
      } finally {
        setDocsLoading(false);
      }
    }
    loadInitialData();
  }, []);

  async function handleCompare() {
    if (selectedDocIds.length < 2) {
      setError("Please select at least two documents to compare.");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const result = await apiRequest(
        "/api/v1/intelligence/compare",
        DocumentComparisonSchema,
        {
          method: "POST",
          body: JSON.stringify({ document_ids: selectedDocIds }),
        },
      );

      setComparison(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Comparison failed. Check document compatibility.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Document Intelligence &amp; Cross-Document Comparison
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Compare multi-document agreements, detect quantity/date discrepancies, and inspect conflicting evidence.
        </p>
      </div>

      {/* Document Selection Card */}
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-gray-100">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-700">
            Select Documents to Compare (min 2)
          </h2>
          <span className="text-xs font-medium text-gray-500">
            Selected: {selectedDocIds.length}
          </span>
        </div>

        {docsLoading ? (
          <p className="text-sm text-gray-400">Loading documents...</p>
        ) : documents.length < 2 ? (
          <EmptyState
            title="Insufficient documents for comparison"
            description="At least two documents must be ingested into the tenant repository to perform cross-document comparisons."
            actionText="Go to Documents"
            onAction={() => router.push("/documents")}
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {documents.map((d) => {
              const isSelected = selectedDocIds.includes(d.doc_id);
              return (
                <div
                  key={d.doc_id}
                  onClick={() => {
                    setSelectedDocIds((prev) =>
                      isSelected ? prev.filter((id) => id !== d.doc_id) : [...prev, d.doc_id],
                    );
                  }}
                  className={`rounded-xl border p-4 cursor-pointer transition flex items-center justify-between ${
                    isSelected
                      ? "border-blue-500 bg-blue-50/40 text-blue-900 shadow-xs ring-1 ring-blue-500"
                      : "border-gray-200 bg-white hover:bg-gray-50 text-gray-800"
                  }`}
                >
                  <div className="truncate mr-2">
                    <p className="text-sm font-semibold truncate">{d.filename}</p>
                    <p className="text-xs text-gray-400 font-mono truncate">{d.doc_id}</p>
                  </div>
                  <span
                    className={`h-5 w-5 rounded-md flex items-center justify-center text-xs font-bold shrink-0 ${
                      isSelected ? "bg-blue-600 text-white" : "border border-gray-300 bg-white"
                    }`}
                  >
                    {isSelected ? "✓" : ""}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        <div className="flex justify-end pt-2">
          <button
            type="button"
            onClick={handleCompare}
            disabled={loading || selectedDocIds.length < 2}
            className="inline-flex items-center rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-blue-500 disabled:opacity-50"
          >
            {loading ? "Comparing Documents..." : "Run Cross-Document Comparison &rarr;"}
          </button>
        </div>
      </div>

      {error && <ErrorState title="Comparison Error" message={error} onRetry={handleCompare} />}

      {/* Comparison Results */}
      {comparison && (
        <div className="space-y-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-xs">
              <span className="text-xs font-medium text-gray-500 uppercase">Compared Pairs</span>
              <p className="mt-1 text-2xl font-bold text-gray-900">{comparison.total_pairs}</p>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-xs">
              <span className="text-xs font-medium text-emerald-600 uppercase">Aligned Values</span>
              <p className="mt-1 text-2xl font-bold text-emerald-700">{comparison.matching_pairs}</p>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-xs">
              <span className="text-xs font-medium text-rose-600 uppercase">Discrepancies / Conflicts</span>
              <p className="mt-1 text-2xl font-bold text-rose-700">{comparison.conflicting_pairs}</p>
            </div>
          </div>

          {/* Conflicts Section */}
          {comparison.conflicts.length > 0 && (
            <div className="rounded-2xl border border-rose-200 bg-rose-50/40 p-6 shadow-xs space-y-4">
              <div className="flex items-center gap-2 pb-2 border-b border-rose-200">
                <span className="text-rose-600 font-bold text-lg">⚠️</span>
                <h3 className="text-base font-semibold text-rose-950">
                  Detected Cross-Document Conflicts ({comparison.conflicts.length})
                </h3>
              </div>
              <div className="space-y-3">
                {comparison.conflicts.map((conf: Record<string, unknown>, i: number) => {
                  const subject = String(conf.subject || "Conflict");
                  const attribute = String(conf.attribute || "");
                  const description = String(conf.description || "");
                  const docIds = (conf.conflicting_document_ids as string[] | undefined) || [];

                  return (
                    <div key={i} className="rounded-xl border border-rose-200 bg-white p-4 shadow-xs">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-2">
                        <div className="font-semibold text-gray-900 text-sm">
                          Conflict: <span className="text-rose-700">{subject} &bull; {attribute}</span>
                        </div>
                        <StatusBadge status="conflict" size="sm" />
                      </div>
                      <p className="text-xs text-gray-600 mb-2">{description}</p>
                      <div className="text-xs font-mono text-gray-500 bg-gray-50 p-2 rounded">
                        Documents involved: {docIds.join(", ")}
                      </div>
                      <div className="mt-3 flex justify-end">
                        <Link
                          href="/reviews"
                          className="inline-flex items-center text-xs font-semibold text-blue-600 hover:text-blue-800"
                        >
                          Open Governance Review Queue &rarr;
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Detailed Alignment Table */}
          <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-xs">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-700">
                Aligned Structured Facts Comparison
              </h3>
              <span className="text-xs text-gray-500 font-mono">{comparison.compared_at}</span>
            </div>
            {comparison.comparisons.length === 0 ? (
              <div className="p-8 text-center text-sm text-gray-500">
                No overlapping structured attributes found between the selected documents.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
                  <thead className="bg-gray-50 text-xs font-semibold uppercase text-gray-500">
                    <tr>
                      <th scope="col" className="px-6 py-3">Subject</th>
                      <th scope="col" className="px-6 py-3">Attribute</th>
                      <th scope="col" className="px-6 py-3">Document A Value</th>
                      <th scope="col" className="px-6 py-3">Document B Value</th>
                      <th scope="col" className="px-6 py-3">Alignment Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {comparison.comparisons.map((item: Record<string, unknown>, idx: number) => {
                      const isMatch = Boolean(item.is_match);
                      const subject = String(item.subject || "");
                      const attribute = String(item.attribute || "");
                      return (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-6 py-3.5 font-medium text-gray-900">{subject}</td>
                          <td className="px-6 py-3.5 text-gray-700">{attribute}</td>
                          <td className="px-6 py-3.5 font-mono text-xs text-gray-800">
                            {String(item.val_a ?? "—")}
                          </td>
                          <td className="px-6 py-3.5 font-mono text-xs text-gray-800">
                            {String(item.val_b ?? "—")}
                          </td>
                          <td className="px-6 py-3.5 whitespace-nowrap">
                            <StatusBadge status={isMatch ? "match" : "conflict"} size="sm" />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
