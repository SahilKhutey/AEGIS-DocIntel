"use client";

import React, { useState, useEffect, Suspense } from "react";
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
import { ComparisonWorkspace } from "@/features/intelligence/components/ComparisonWorkspace";
import { ComparisonResult } from "@/features/intelligence/components/ComparisonResult";
import type { ComparisonResponse, ComparisonDifference } from "@/features/intelligence/types";

function CompareContent() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<DocumentComparison | null>(null);
  const [domainComparison, setDomainComparison] = useState<ComparisonResponse | null>(null);
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
    void loadInitialData();
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

      // Build domain model
      const diffs: ComparisonDifference[] = [];
      (result.conflicts || []).forEach((conf: Record<string, unknown>, idx: number) => {
        diffs.push({
          differenceId: `diff-conf-${idx}`,
          category: String(conf.attribute || conf.subject || "Discrepancy"),
          description: String(conf.description || `Discrepancy in ${String(conf.attribute || "attribute")}`),
          significance: "high",
        });
      });
      (result.comparisons || []).forEach((comp: Record<string, unknown>, idx: number) => {
        if (!comp.is_match) {
          diffs.push({
            differenceId: `diff-comp-${idx}`,
            category: String(comp.attribute || "Fact"),
            description: `Value variance: "${String(comp.val_a ?? "—")}" vs "${String(comp.val_b ?? "—")}"`,
            significance: "medium",
          });
        }
      });

      setDomainComparison({
        comparisonId: `cmp-${Date.now()}`,
        documentIds: result.document_ids,
        differences: diffs,
        summary: `Compared ${result.total_pairs} pairs across ${result.document_ids.length} documents. Found ${result.matching_pairs} matches and ${result.conflicting_pairs} conflicts.`,
      });
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

      {/* Document Selection Workspace */}
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
        <ComparisonWorkspace
          documents={documents}
          selectedDocIds={selectedDocIds}
          onToggleDoc={(docId) => {
            setSelectedDocIds((prev) =>
              prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId],
            );
          }}
          onCompare={() => void handleCompare()}
          isLoading={loading}
        />
      )}

      {error && (
        <ErrorState
          title="Comparison Failed"
          message={error}
          onRetry={() => { void handleCompare(); }}
        />
      )}

      {/* Domain Differences & Discrepancies */}
      {domainComparison && (
        <ComparisonResult
          result={domainComparison}
          onOpenDocument={(docId) => router.push(`/documents/${encodeURIComponent(docId)}`)}
        />
      )}

      {/* Detailed Alignment & Conflicts Table */}
      {comparison && (
        <div className="space-y-8">
          {/* Detected Conflicts */}
          {comparison.conflicts.length > 0 && (
            <div className="rounded-2xl border border-rose-200 bg-rose-50/40 p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-rose-100">
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

export default function ComparePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gray-500">Loading Compare Workspace...</div>}>
      <CompareContent />
    </Suspense>
  );
}
