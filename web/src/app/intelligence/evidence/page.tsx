"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { DocumentListSchema, type DocumentItem } from "@/lib/schemas";
import { apiRequest } from "@/lib/api-client";
import { ApiError } from "@/lib/errors";
import { getDocumentEvidence } from "@/features/intelligence/api/evidence.api";
import { EvidenceDetail } from "@/features/intelligence/components/EvidenceDetail";
import type { EvidenceRecord } from "@/features/intelligence/types";
import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";

function EvidenceContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialDocId = searchParams.get("document_id") || "";
  const initialPassageId = searchParams.get("passage_id") || "";

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>(initialDocId);
  const [evidenceList, setEvidenceList] = useState<EvidenceRecord[]>([]);
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
        if (!selectedDocId && docs.length > 0) {
          setSelectedDocId(docs[0].doc_id);
        }
      } catch {
        // Continue even if docs fail
      } finally {
        setDocsLoading(false);
      }
    }
    void loadDocs();
  }, [selectedDocId]);

  useEffect(() => {
    if (!selectedDocId) return;

    async function loadEvidence() {
      try {
        setLoading(true);
        setError(null);
        const records = await getDocumentEvidence(selectedDocId);
        setEvidenceList(records);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load evidence for document.");
      } finally {
        setLoading(false);
      }
    }
    void loadEvidence();
  }, [selectedDocId]);

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Evidence Explorer &amp; Provenance
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Inspect verbatim source passages, page-level coordinates, and ground truth provenance across authorized documents.
        </p>
      </div>

      {/* Document Selection Banner */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <label htmlFor="evidence-doc-select" className="text-xs font-semibold uppercase tracking-wider text-gray-500 block mb-1">
            Active Document Evidence Scope
          </label>
          <select
            id="evidence-doc-select"
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            disabled={docsLoading || documents.length === 0}
            className="rounded-xl border border-gray-300 bg-white px-3.5 py-2 text-sm text-gray-800 font-medium focus:border-blue-500 focus:outline-none min-w-[260px]"
          >
            {documents.length === 0 ? (
              <option value="">No documents ingested</option>
            ) : (
              documents.map((d) => (
                <option key={d.doc_id} value={d.doc_id}>
                  {d.filename} ({d.doc_id.slice(0, 8)}...)
                </option>
              ))
            )}
          </select>
        </div>

        {selectedDocId && (
          <button
            type="button"
            onClick={() => router.push(`/documents/${encodeURIComponent(selectedDocId)}`)}
            className="inline-flex items-center text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline self-start sm:self-auto"
          >
            Open Complete Document View &rarr;
          </button>
        )}
      </div>

      {/* Error state */}
      {error && (
        <ErrorState
          title="Evidence Load Error"
          message={error}
          onRetry={() => {
            if (selectedDocId) {
              const current = selectedDocId;
              setSelectedDocId("");
              setTimeout(() => setSelectedDocId(current), 10);
            }
          }}
        />
      )}

      {/* Content */}
      {loading ? (
        <div className="p-8 text-center text-sm text-gray-400">Loading document evidence passages...</div>
      ) : evidenceList.length === 0 && !error ? (
        <EmptyState
          title="No evidence records available"
          description="The selected document currently has no indexed evidence passages or chunks."
          actionText="Ingest or View Documents"
          onAction={() => router.push("/documents")}
        />
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-700">
              Verified Evidence Passages ({evidenceList.length})
            </h2>
            <span className="text-xs text-emerald-700 font-medium bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
              Verbatim Ground Truth
            </span>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {evidenceList.map((ev) => {
              const isTargetPassage = initialPassageId && ev.passageId === initialPassageId;
              return (
                <div
                  key={ev.evidenceId}
                  className={isTargetPassage ? "ring-2 ring-blue-500 rounded-xl" : ""}
                >
                  <EvidenceDetail
                    evidence={ev}
                    onOpenDocument={(docId) => {
                      router.push(`/documents/${encodeURIComponent(docId)}`);
                    }}
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default function EvidencePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gray-500">Loading Evidence Explorer...</div>}>
      <EvidenceContent />
    </Suspense>
  );
}
