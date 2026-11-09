"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter } from "next/navigation";
import { DocumentListSchema, type DocumentItem } from "@/lib/schemas";
import { apiRequest } from "@/lib/api-client";
import { ApiError } from "@/lib/errors";
import { getKnowledgeGraph } from "@/features/intelligence/api/knowledge.api";
import { KnowledgeGraph } from "@/features/intelligence/components/KnowledgeGraph";
import type { KnowledgeGraphResponse } from "@/features/intelligence/types";
import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";

function KnowledgeContent() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [graphData, setGraphData] = useState<KnowledgeGraphResponse>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(false);
  const [docsLoading, setDocsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDocs() {
      try {
        setDocsLoading(true);
        const data = await apiRequest("/api/v1/documents", DocumentListSchema);
        const docs = data.items || [];
        setDocuments(docs);
        if (docs.length > 0) {
          // Default select the first 2 documents
          setSelectedDocIds(docs.slice(0, 2).map((d) => d.doc_id));
        }
      } catch {
        // Continue even if documents fail
      } finally {
        setDocsLoading(false);
      }
    }
    void loadDocs();
  }, []);

  useEffect(() => {
    if (selectedDocIds.length === 0) {
      setGraphData({ nodes: [], edges: [] });
      return;
    }

    async function loadGraph() {
      try {
        setLoading(true);
        setError(null);
        const res = await getKnowledgeGraph(selectedDocIds);
        setGraphData(res);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load knowledge graph.");
      } finally {
        setLoading(false);
      }
    }
    void loadGraph();
  }, [selectedDocIds]);

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Knowledge Graph &amp; Entity Relationships
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Explore extracted concepts, structured entities, and verified cross-document connections with accessible tabular alternative.
        </p>
      </div>

      {/* Scope Selector */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold uppercase tracking-wider text-gray-500">
            Included Document Scope ({selectedDocIds.length} Selected)
          </label>
          {documents.length > 0 && (
            <button
              type="button"
              onClick={() =>
                setSelectedDocIds(
                  selectedDocIds.length === documents.length
                    ? []
                    : documents.map((d) => d.doc_id),
                )
              }
              className="text-xs font-semibold text-blue-600 hover:text-blue-800"
            >
              {selectedDocIds.length === documents.length ? "Deselect All" : "Select All"}
            </button>
          )}
        </div>

        {docsLoading ? (
          <p className="text-xs text-gray-400">Loading documents...</p>
        ) : documents.length === 0 ? (
          <p className="text-xs text-gray-500">No documents ingested.</p>
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
                      ? "bg-blue-600 text-white border-blue-600 shadow-xs"
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

      {/* Error State */}
      {error && (
        <ErrorState
          title="Graph Loading Error"
          message={error}
          onRetry={() => {
            const current = [...selectedDocIds];
            setSelectedDocIds([]);
            setTimeout(() => setSelectedDocIds(current), 10);
          }}
        />
      )}

      {/* Main Content */}
      {loading ? (
        <div className="p-12 text-center text-sm text-gray-400">Constructing document knowledge graph...</div>
      ) : selectedDocIds.length === 0 ? (
        <EmptyState
          title="Select documents to visualize"
          description="Choose at least one authorized document above to inspect its entity-relationship graph."
        />
      ) : (
        <KnowledgeGraph
          nodes={graphData.nodes}
          edges={graphData.edges}
          onOpenDocument={(docId) => router.push(`/documents/${encodeURIComponent(docId)}`)}
        />
      )}
    </div>
  );
}

export default function KnowledgePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gray-500">Loading Knowledge Graph...</div>}>
      <KnowledgeContent />
    </Suspense>
  );
}
