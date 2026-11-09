"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { DocumentListSchema, type DocumentItem } from "@/lib/schemas";
import { apiRequest } from "@/lib/api-client";
import { ApiError } from "@/lib/errors";
import { RetrievalSearch } from "@/features/intelligence/components/RetrievalSearch";
import { RetrievalResult } from "@/features/intelligence/components/RetrievalResult";
import { retrieveDocuments } from "@/features/intelligence/api/retrieval.api";
import type { RetrievalResult as ResultType } from "@/features/intelligence/types";
import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";

function RetrievalContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";
  const initialDocId = searchParams.get("doc_id") || "";

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>(initialDocId);
  const [results, setResults] = useState<ResultType[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastQuery, setLastQuery] = useState(initialQuery);

  useEffect(() => {
    async function loadDocs() {
      try {
        const data = await apiRequest("/api/v1/documents", DocumentListSchema);
        setDocuments(data.items || []);
      } catch {
        // Continue even if document list fails to load
      }
    }
    void loadDocs();
  }, []);

  async function handleSearch(query: string) {
    if (!query.trim()) return;
    setLastQuery(query);
    setLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const resp = await retrieveDocuments({
        query: query.trim(),
        documentIds: selectedDocId ? [selectedDocId] : undefined,
      });
      setResults(resp.results || []);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Retrieval query failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Document Retrieval Interface
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Search across authorized passages, inspect hybrid BM25 and vector ranking, and trace passage provenance.
        </p>
      </div>

      {/* Scope and Search Form Card */}
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <label htmlFor="scope-select" className="text-xs font-semibold uppercase tracking-wider text-gray-500">
            Document Scope Filter
          </label>
          <select
            id="scope-select"
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs text-gray-700 focus:border-blue-500 focus:outline-none"
          >
            <option value="">All Tenant Documents</option>
            {documents.map((d) => (
              <option key={d.doc_id} value={d.doc_id}>
                {d.filename}
              </option>
            ))}
          </select>
        </div>

        <RetrievalSearch onSearch={(q) => void handleSearch(q)} loading={loading} />
      </div>

      {/* Error state */}
      {error && (
        <ErrorState
          title="Retrieval Error"
          message={error}
          onRetry={() => { void handleSearch(lastQuery); }}
        />
      )}

      {/* Results or Empty States */}
      {!hasSearched ? (
        <EmptyState
          title="Ready to search"
          description="Submit a search query above to inspect retrieved passages and hybrid ranking relevance."
        />
      ) : results.length === 0 && !loading && !error ? (
        <EmptyState
          title="No matching passages found"
          description={`No document passages matched query "${lastQuery}". Try broader keywords or clearing the document scope filter.`}
        />
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-700">
              Retrieved Passages ({results.length})
            </h2>
            <span className="text-xs text-gray-400">Ranked by backend relevance</span>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {results.map((res) => (
              <RetrievalResult
                key={res.resultId}
                result={res}
                onOpenEvidence={(passageId, docId) => {
                  router.push(
                    `/intelligence/evidence?document_id=${encodeURIComponent(docId)}&passage_id=${encodeURIComponent(passageId)}`,
                  );
                }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function RetrievalPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gray-500">Loading Retrieval Interface...</div>}>
      <RetrievalContent />
    </Suspense>
  );
}
