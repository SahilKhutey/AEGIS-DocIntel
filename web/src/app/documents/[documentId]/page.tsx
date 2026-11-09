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
  const [message, setMessage] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const inspectionData = await defaultDocumentService.getInspection(documentId);
      setInspection(inspectionData);

      // Load existing facts
      try {
        const encodedId = encodeURIComponent(documentId);
        const factsData = await apiRequest(
          `/api/v1/documents/${encodedId}/facts`,
          z.object({ facts: z.array(ExtractedFactSchema) }),
        );
        setFacts(factsData.facts || []);
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
      const encodedId = encodeURIComponent(documentId);
      const res = await apiRequest(
        `/api/v1/documents/${encodedId}/extract-facts`,
        z.object({ facts: z.array(ExtractedFactSchema), fact_count: z.number().optional() }),
        { method: "POST" },
      );
      setFacts(res.facts || []);
      setMessage(`Successfully extracted ${res.facts.length} facts.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to extract facts.");
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
