"use client";

import React, { useEffect, useState, useCallback, use } from "react";
import Link from "next/link";
import { defaultDocumentService } from "@/features/documents/api";
import { DocumentInspector } from "@/features/documents/components/document-inspector";
import type { DocumentInspection } from "@/features/documents/types";
import { ExtractedFactSchema, type ExtractedFact } from "@/lib/schemas";
import { apiRequest } from "@/lib/api-client";
import { ApiError } from "@/lib/errors";
import { ErrorState } from "@/components/error-state";
import { z } from "zod";

interface PageProps {
  params: Promise<{ documentId: string }>;
}

function DocumentDetailContent({ params }: PageProps) {
  const { documentId } = use(params);

  const [inspection, setInspection] = useState<DocumentInspection | null>(null);
  const [facts, setFacts] = useState<ExtractedFact[]>([]);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setExtractionError(null);

      const inspectionData = await defaultDocumentService.getInspection(documentId);
      setInspection(inspectionData);

      // Load existing facts
      try {
        const encodedId = encodeURIComponent(documentId);
        const factsData = await apiRequest(
          `/api/v1/documents/${encodedId}/facts`,
          z.union([
            z.object({ facts: z.array(ExtractedFactSchema) }),
            z.array(ExtractedFactSchema),
          ]),
        );
        const factList = Array.isArray(factsData) ? factsData : factsData.facts || [];
        setFacts(factList);
      } catch {
        // Facts optional
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Document not found or inaccessible.");
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleExtractFacts() {
    try {
      setExtracting(true);
      setMessage(null);
      setExtractionError(null);
      const encodedId = encodeURIComponent(documentId);
      const res = await apiRequest(
        `/api/v1/documents/${encodedId}/extract-facts`,
        z.object({
          status: z.string().optional(),
          facts: z.array(ExtractedFactSchema).default([]),
          errors: z.array(z.string()).optional(),
          document_id: z.string().optional(),
        }),
        {
          method: "POST",
          body: JSON.stringify({ schema_name: "contract_terms" }),
        },
      );

      if (res.status === "failed" && (!res.facts || res.facts.length === 0)) {
        const errorMsg =
          res.errors && res.errors.length > 0
            ? res.errors.join(". ")
            : "No structured facts could be extracted from this document.";
        setExtractionError(errorMsg);
        return;
      }

      setFacts(res.facts || []);
      setMessage(`Successfully extracted ${res.facts.length} facts.`);
    } catch (err) {
      setExtractionError(err instanceof ApiError ? err.message : "Failed to extract facts.");
    } finally {
      setExtracting(false);
    }
  }

  if (loading) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-12 text-center" aria-busy="true">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-[var(--primary)] border-r-transparent" />
        <p className="mt-4 text-sm font-medium text-[var(--muted)]">Loading document details...</p>
      </div>
    );
  }

  if (error || !inspection) {
    return (
      <div className="space-y-4">
        <Link href="/documents" className="text-sm font-medium text-[var(--primary)] hover:underline">
          &larr; Back to documents
        </Link>
        <ErrorState title="Document Inaccessible" message={error || "Document not found"} onRetry={loadData} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {message && (
        <div role="status" className="rounded-lg bg-emerald-50 border border-emerald-200 p-3 text-sm text-emerald-800">
          {message}
        </div>
      )}

      {extractionError && (
        <div role="alert" className="rounded-lg bg-rose-50 border border-rose-200 p-3 text-sm text-rose-800 flex items-center justify-between">
          <span>{extractionError}</span>
          <button
            type="button"
            onClick={() => setExtractionError(null)}
            className="text-rose-600 hover:text-rose-800 text-xs font-semibold ml-4"
          >
            Dismiss
          </button>
        </div>
      )}

      <DocumentInspector
        data={inspection}
        facts={facts}
        onExtractFacts={handleExtractFacts}
        extractingFacts={extracting}
      />
    </div>
  );
}

export default function DocumentDetailPage(props: PageProps) {
  return (
    <React.Suspense fallback={<div className="p-8 text-center text-[var(--muted)]">Loading document details...</div>}>
      <DocumentDetailContent {...props} />
    </React.Suspense>
  );
}
