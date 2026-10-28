"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  DocumentSchema,
  DocumentChunkListSchema,
  type DocumentItem,
  type DocumentChunk,
  ExtractedFactSchema,
  type ExtractedFact,
} from "@/lib/schemas";
import { apiRequest } from "@/lib/api-client";
import { ApiError } from "@/lib/errors";
import { StatusBadge } from "@/components/status-badge";
import { ErrorState } from "@/components/error-state";
import { z } from "zod";

interface PageProps {
  params: Promise<{ documentId: string }>;
}

function DocumentDetailContent({ params }: PageProps) {
  const { documentId } = use(params);

  const [doc, setDoc] = useState<DocumentItem | null>(null);
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [facts, setFacts] = useState<ExtractedFact[]>([]);
  const [activeTab, setActiveTab] = useState<"chunks" | "facts">("chunks");
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);

      const encodedId = encodeURIComponent(documentId);

      // Load document metadata
      const docData = await apiRequest(`/api/v1/documents/${encodedId}`, DocumentSchema);
      setDoc(docData);

      // Load chunks if available
      try {
        const chunkData = await apiRequest(
          `/api/v1/documents/${encodedId}/chunks`,
          DocumentChunkListSchema,
        );
        setChunks(chunkData.items || []);
      } catch {
        // Chunks optional or empty
      }

      // Load existing facts
      try {
        const factsData = await apiRequest(
          `/api/v1/documents/${encodedId}/facts`,
          z.object({ facts: z.array(ExtractedFactSchema) }),
        );
        setFacts(factsData.facts || []);
      } catch {
        // Facts optional or empty
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Document not found or inaccessible.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [documentId]);

  async function handleExtractFacts() {
    try {
      setExtracting(true);
      setMessage(null);
      const encodedId = encodeURIComponent(documentId);
      const res = await apiRequest(
        `/api/v1/documents/${encodedId}/extract-facts`,
        z.object({ facts: z.array(ExtractedFactSchema), fact_count: z.number().optional() }),
        { method: "POST" },
      );
      setFacts(res.facts || []);
      setMessage(`Successfully extracted ${res.facts.length} facts.`);
      setActiveTab("facts");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to extract facts.");
    } finally {
      setExtracting(false);
    }
  }

  if (loading) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-12 text-center" aria-busy="true">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent" />
        <p className="mt-4 text-sm font-medium text-gray-600">Loading document details...</p>
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div className="space-y-4">
        <Link href="/documents" className="text-sm font-medium text-blue-600 hover:underline">
          &larr; Back to documents
        </Link>
        <ErrorState title="Document Inaccessible" message={error || "Document not found"} onRetry={loadData} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb & Navigation */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/documents" className="hover:text-blue-600">
          Documents
        </Link>
        <span>/</span>
        <span className="text-gray-900 font-medium truncate max-w-sm">{doc.filename}</span>
      </div>

      {/* Header Card */}
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900">{doc.filename}</h1>
              <StatusBadge status={doc.status} />
            </div>
            <p className="text-xs font-mono text-gray-400 mt-1">ID: {doc.doc_id}</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleExtractFacts}
              disabled={extracting}
              className="inline-flex items-center rounded-lg border border-purple-200 bg-purple-50 px-3.5 py-2 text-sm font-semibold text-purple-700 hover:bg-purple-100 disabled:opacity-50"
            >
              {extracting ? "Extracting Facts..." : "Extract Structured Facts"}
            </button>
            <Link
              href={`/ask?doc_id=${encodeURIComponent(doc.doc_id)}`}
              className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-xs hover:bg-blue-500"
            >
              Ask on this Document &rarr;
            </Link>
          </div>
        </div>

        {/* Metadata Grid */}
        <dl className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4 border-t border-gray-100 pt-4 text-xs">
          <div>
            <dt className="text-gray-500 font-medium">Pages</dt>
            <dd className="mt-1 text-sm font-semibold text-gray-900">{doc.page_count ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-gray-500 font-medium">Chunks Indexed</dt>
            <dd className="mt-1 text-sm font-semibold text-gray-900">{doc.chunk_count ?? chunks.length}</dd>
          </div>
          <div>
            <dt className="text-gray-500 font-medium">Language</dt>
            <dd className="mt-1 text-sm font-semibold text-gray-900 uppercase">{doc.language}</dd>
          </div>
          <div>
            <dt className="text-gray-500 font-medium">Ingested At</dt>
            <dd className="mt-1 text-sm font-semibold text-gray-900">
              {new Date(doc.created_at).toLocaleString()}
            </dd>
          </div>
        </dl>
      </div>

      {message && (
        <div role="status" className="rounded-lg bg-emerald-50 border border-emerald-200 p-3 text-sm text-emerald-800">
          {message}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8" aria-label="Tabs">
          <button
            type="button"
            onClick={() => setActiveTab("chunks")}
            className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === "chunks"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            Chunks &amp; Passages ({chunks.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("facts")}
            className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === "facts"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            Structured Facts ({facts.length})
          </button>
        </nav>
      </div>

      {/* Tab Panels */}
      {activeTab === "chunks" ? (
        chunks.length === 0 ? (
          <div className="rounded-xl border border-gray-200 bg-white p-8 text-center text-sm text-gray-500">
            No text chunks found for this document.
          </div>
        ) : (
          <div className="space-y-3">
            {chunks.map((chunk, idx) => (
              <div
                key={chunk.chunk_id || idx}
                className="rounded-xl border border-gray-200 bg-white p-4 shadow-xs"
              >
                <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
                  <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">
                    Chunk {idx + 1}: {chunk.chunk_id}
                  </span>
                  <span>{chunk.page_number != null ? `Page ${chunk.page_number}` : ""}</span>
                </div>
                <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">{chunk.text}</p>
              </div>
            ))}
          </div>
        )
      ) : (
        facts.length === 0 ? (
          <div className="rounded-xl border border-gray-200 bg-white p-8 text-center">
            <p className="text-sm text-gray-500 mb-3">No structured facts extracted yet.</p>
            <button
              type="button"
              onClick={handleExtractFacts}
              disabled={extracting}
              className="rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white shadow-xs hover:bg-blue-500"
            >
              Run Fact Extraction
            </button>
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xs">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
                <thead className="bg-gray-50 text-xs font-semibold uppercase text-gray-500">
                  <tr>
                    <th scope="col" className="px-6 py-3">Subject</th>
                    <th scope="col" className="px-6 py-3">Attribute</th>
                    <th scope="col" className="px-6 py-3">Value</th>
                    <th scope="col" className="px-6 py-3">Type / Unit</th>
                    <th scope="col" className="px-6 py-3">Evidence Quote</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {facts.map((fact) => {
                    const quote = fact.evidence?.[0]?.quoted_text as string || fact.raw_value;
                    return (
                      <tr key={fact.fact_id} className="hover:bg-gray-50">
                        <td className="px-6 py-3.5 font-medium text-gray-900">{fact.subject}</td>
                        <td className="px-6 py-3.5 text-gray-700">{fact.attribute}</td>
                        <td className="px-6 py-3.5 font-semibold text-blue-700">
                          {String(fact.value)}
                        </td>
                        <td className="px-6 py-3.5 text-xs text-gray-500">
                          {fact.value_type} {fact.unit ? `(${fact.unit})` : ""}
                        </td>
                        <td className="px-6 py-3.5 text-xs text-gray-600 max-w-sm italic truncate">
                          &ldquo;{quote}&rdquo;
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )
      )}
    </div>
  );
}

export default function DocumentDetailPage(props: PageProps) {
  return (
    <React.Suspense fallback={<div className="p-8 text-center text-gray-500">Loading document details...</div>}>
      <DocumentDetailContent {...props} />
    </React.Suspense>
  );
}
