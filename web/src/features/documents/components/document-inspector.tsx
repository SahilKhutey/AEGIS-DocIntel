"use client";

import { useState } from "react";
import Link from "next/link";
import {
  FileText,
  ArrowLeft,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { DocumentStatusBadge } from "./document-status";
import type { DocumentInspection, ExtractedTextPage } from "../types";
import type { ExtractedFact } from "@/lib/schemas";

type InspectorTab =
  | "overview"
  | "preview"
  | "text"
  | "facts"
  | "metadata"
  | "processing";

export type DocumentInspectorProps = {
  data: DocumentInspection;
  facts?: ExtractedFact[];
  onExtractFacts?: () => Promise<void>;
  extractingFacts?: boolean;
};

const tabs: Array<{
  id: InspectorTab;
  label: string;
}> = [
  { id: "overview", label: "Overview" },
  { id: "preview", label: "Preview" },
  { id: "text", label: "Extracted Text & Chunks" },
  { id: "facts", label: "Extracted Facts" },
  { id: "metadata", label: "Metadata" },
  { id: "processing", label: "Processing Summary" },
];

export function DocumentInspector({
  data,
  facts = [],
  onExtractFacts,
  extractingFacts = false,
}: DocumentInspectorProps) {
  const [activeTab, setActiveTab] = useState<InspectorTab>("overview");

  return (
    <div className="space-y-6">
      {/* Top Header & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[var(--border)] pb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/documents"
            className="rounded-lg border border-[var(--border)] p-2 text-[var(--muted)] hover:bg-[var(--surface-muted)] hover:text-[var(--foreground)]"
            title="Back to Document Library"
            aria-label="Back to Document Library"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)] break-words">
                {data.document.name}
              </h1>
              <DocumentStatusBadge status={data.document.status} />
            </div>
            <p className="text-xs text-[var(--muted)] mt-1">
              Document details &middot; ID: {data.document.id} &middot;{" "}
              {data.document.mimeType} &middot;{" "}
              {(data.document.sizeBytes / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {onExtractFacts && (
            <Button
              type="button"
              variant="outline"
              disabled={extractingFacts}
              onClick={() => void onExtractFacts()}
            >
              <Sparkles className="mr-2 h-4 w-4 text-[var(--primary)]" />
              {extractingFacts ? "Extracting..." : "Extract Structured Facts"}
            </Button>
          )}
          <Link
            href={`/ask?doc_id=${encodeURIComponent(data.document.id)}`}
            className="inline-flex items-center rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-semibold text-[var(--primary-foreground)] shadow-xs hover:opacity-90 transition-opacity"
          >
            Ask on this Document &rarr;
          </Link>
        </div>
      </div>

      {/* Tab Navigation List */}
      <div
        role="tablist"
        aria-label="Document inspection sections"
        className="flex gap-2 overflow-x-auto border-b border-[var(--border)]"
      >
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={`panel-${tab.id}`}
              id={`tab-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              className={[
                "whitespace-nowrap border-b-2 px-3.5 py-2.5 text-sm font-medium transition-colors outline-none",
                isActive
                  ? "border-[var(--primary)] text-[var(--primary)] font-semibold"
                  : "border-transparent text-[var(--muted)] hover:text-[var(--foreground)]",
              ].join(" ")}
            >
              {tab.label}
              {tab.id === "text" && data.extractedPages && (
                <span className="ml-1.5 rounded-full bg-[var(--surface-muted)] px-2 py-0.5 text-xs text-[var(--muted)]">
                  {data.extractedPages.length}
                </span>
              )}
              {tab.id === "facts" && facts.length > 0 && (
                <span className="ml-1.5 rounded-full bg-[var(--surface-muted)] px-2 py-0.5 text-xs text-[var(--muted)]">
                  {facts.length}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      <div
        id={`panel-${activeTab}`}
        role="tabpanel"
        aria-labelledby={`tab-${activeTab}`}
        className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs min-h-72"
      >
        {activeTab === "overview" && (
          <div className="space-y-6">
            <div>
              <h2 className="text-base font-semibold text-[var(--foreground)]">
                Document Overview
              </h2>
              <p className="text-sm text-[var(--muted)] mt-0.5">
                Core identity, indexing lifecycle, and provenance.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] p-4">
                <span className="text-xs text-[var(--muted)]">Document Status</span>
                <div className="mt-1">
                  <DocumentStatusBadge status={data.document.status} />
                </div>
              </div>

              <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] p-4">
                <span className="text-xs text-[var(--muted)]">Page Count</span>
                <p className="mt-1 text-lg font-semibold tabular-nums text-[var(--foreground)]">
                  {data.document.pageCount || data.metadata.pageCount || 1}
                </p>
              </div>

              <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] p-4">
                <span className="text-xs text-[var(--muted)]">Chunk Count</span>
                <p className="mt-1 text-lg font-semibold tabular-nums text-[var(--foreground)]">
                  {data.document.chunkCount || data.extractedPages?.length || 0}
                </p>
              </div>

              <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] p-4">
                <span className="text-xs text-[var(--muted)]">Ingested At</span>
                <p className="mt-1 text-sm font-medium text-[var(--foreground)]">
                  {new Date(data.document.createdAt).toLocaleString()}
                </p>
              </div>

              <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] p-4">
                <span className="text-xs text-[var(--muted)]">Last Processed</span>
                <p className="mt-1 text-sm font-medium text-[var(--foreground)]">
                  {new Date(data.document.updatedAt).toLocaleString()}
                </p>
              </div>

              <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] p-4">
                <span className="text-xs text-[var(--muted)]">MIME Format</span>
                <p className="mt-1 text-sm font-medium text-[var(--foreground)]">
                  {data.document.mimeType}
                </p>
              </div>
            </div>

            {data.extractedPages && data.extractedPages.length > 0 && (
              <div className="space-y-3 pt-4 border-t border-[var(--border)]">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-[var(--foreground)]">
                    Indexed Chunks &amp; Passages
                  </h3>
                  <button
                    type="button"
                    onClick={() => setActiveTab("text")}
                    className="text-xs text-[var(--primary)] hover:underline"
                  >
                    View all chunks ({data.extractedPages.length}) &rarr;
                  </button>
                </div>
                <div className="space-y-3">
                  {data.extractedPages.slice(0, 3).map((page: ExtractedTextPage) => (
                    <article
                      key={page.chunkId || page.pageNumber}
                      className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] p-4 space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-xs font-semibold text-[var(--muted)]">
                        <span>
                          {page.sectionTitle ? (
                            <strong className="text-[var(--foreground)]">{page.sectionTitle}</strong>
                          ) : (
                            `Page ${page.pageNumber}`
                          )}
                        </span>
                        {page.chunkId && <span className="font-mono text-xs">{page.chunkId}</span>}
                      </div>
                      <p className="text-sm leading-relaxed text-[var(--foreground)] whitespace-pre-wrap">
                        {page.text}
                      </p>
                    </article>
                  ))}
                </div>
              </div>
            )}

            {facts && facts.length > 0 && (
              <div className="space-y-3 pt-4 border-t border-[var(--border)]">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-[var(--foreground)]">
                    Extracted Facts
                  </h3>
                  <button
                    type="button"
                    onClick={() => setActiveTab("facts")}
                    className="text-xs text-[var(--primary)] hover:underline"
                  >
                    View all facts ({facts.length}) &rarr;
                  </button>
                </div>
                <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-[var(--border)] bg-[var(--surface-muted)] text-xs font-semibold uppercase text-[var(--muted)]">
                      <tr>
                        <th scope="col" className="p-2.5">Subject</th>
                        <th scope="col" className="p-2.5">Attribute</th>
                        <th scope="col" className="p-2.5">Value</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--border)]">
                      {facts.slice(0, 5).map((fact) => (
                        <tr key={fact.fact_id} className="hover:bg-[var(--surface-muted)]">
                          <td className="p-2.5 font-medium text-[var(--foreground)]">{fact.subject}</td>
                          <td className="p-2.5 text-[var(--muted)]">{fact.attribute}</td>
                          <td className="p-2.5 font-semibold text-[var(--foreground)]">
                            {fact.raw_value || String(fact.value)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "preview" && (
          <div className="space-y-4">
            <div>
              <h2 className="text-base font-semibold text-[var(--foreground)]">
                Source Document Preview
              </h2>
              <p className="text-sm text-[var(--muted)] mt-0.5">
                Authentic visual preview of the uploaded source file.
              </p>
            </div>

            {data.previewAvailable ? (
              <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] p-8 text-center min-h-80 flex flex-col items-center justify-center">
                <FileText className="h-12 w-12 text-[var(--primary)] mb-3" />
                <p className="text-sm font-medium text-[var(--foreground)]">
                  {data.document.name}
                </p>
                <p className="text-xs text-[var(--muted)] mt-1">
                  Secure in-browser preview available for authorized analytical review.
                </p>
              </div>
            ) : (
              <div className="rounded-lg border border-dashed border-[var(--border)] p-8 text-center">
                <p className="text-sm text-[var(--muted)]">
                  Preview is unavailable or format ({data.document.mimeType}) does not support direct browser rendering.
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === "text" && (
          <div className="space-y-4">
            <div>
              <h2 className="text-base font-semibold text-[var(--foreground)]">
                Extracted Text &amp; Chunks
              </h2>
              <p className="text-sm text-[var(--muted)] mt-0.5">
                Text passages extracted and indexed from document pages.
              </p>
            </div>

            {(!data.extractedPages || data.extractedPages.length === 0) ? (
              <div className="rounded-lg border border-dashed border-[var(--border)] p-8 text-center text-sm text-[var(--muted)]">
                No text chunks have been indexed for this document yet.
              </div>
            ) : (
              <div className="space-y-3">
                {data.extractedPages.map((page: ExtractedTextPage) => (
                  <article
                    key={page.chunkId || page.pageNumber}
                    className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] p-4 space-y-2"
                  >
                    <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
                      <span>Page {page.pageNumber}</span>
                      {page.chunkId && <span className="font-mono">{page.chunkId}</span>}
                    </div>
                    <p className="text-sm leading-relaxed text-[var(--foreground)] whitespace-pre-wrap">
                      {page.text}
                    </p>
                  </article>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "facts" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-semibold text-[var(--foreground)]">
                  Extracted Facts &amp; Entities
                </h2>
                <p className="text-sm text-[var(--muted)] mt-0.5">
                  Structured statements extracted from document passages.
                </p>
              </div>
            </div>

            {facts.length === 0 ? (
              <div className="rounded-lg border border-dashed border-[var(--border)] p-8 text-center text-sm text-[var(--muted)]">
                No structured facts extracted yet. Click &quot;Extract Facts&quot; to initiate extraction.
              </div>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-[var(--border)] bg-[var(--surface-muted)] text-xs font-semibold uppercase text-[var(--muted)]">
                    <tr>
                      <th scope="col" className="p-3">Subject</th>
                      <th scope="col" className="p-3">Attribute</th>
                      <th scope="col" className="p-3">Value</th>
                      <th scope="col" className="p-3">Confidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border)]">
                    {facts.map((fact) => (
                      <tr key={fact.fact_id} className="hover:bg-[var(--surface-muted)]">
                        <td className="p-3 font-medium text-[var(--foreground)]">{fact.subject}</td>
                        <td className="p-3 text-[var(--muted)]">{fact.attribute}</td>
                        <td className="p-3 font-semibold text-[var(--foreground)]">
                          {fact.raw_value || String(fact.value)}
                        </td>
                        <td className="p-3 text-xs text-[var(--muted)] tabular-nums">
                          {Math.round((fact.confidence || 1.0) * 100)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === "metadata" && (
          <div className="space-y-4">
            <div>
              <h2 className="text-base font-semibold text-[var(--foreground)]">
                Document Metadata
              </h2>
              <p className="text-sm text-[var(--muted)] mt-0.5">
                Technical file attributes and parsed metadata properties.
              </p>
            </div>

            <div className="rounded-lg border border-[var(--border)] divide-y divide-[var(--border)] text-sm">
              <div className="grid grid-cols-3 p-3">
                <span className="text-[var(--muted)]">File Name</span>
                <span className="col-span-2 font-medium text-[var(--foreground)]">{data.document.name}</span>
              </div>
              <div className="grid grid-cols-3 p-3">
                <span className="text-[var(--muted)]">MIME Type</span>
                <span className="col-span-2 font-medium text-[var(--foreground)]">{data.document.mimeType}</span>
              </div>
              <div className="grid grid-cols-3 p-3">
                <span className="text-[var(--muted)]">File Size</span>
                <span className="col-span-2 font-medium text-[var(--foreground)]">
                  {(data.document.sizeBytes / 1024 / 1024).toFixed(2)} MB ({data.document.sizeBytes} bytes)
                </span>
              </div>
              <div className="grid grid-cols-3 p-3">
                <span className="text-[var(--muted)]">Document ID</span>
                <span className="col-span-2 font-mono text-xs text-[var(--foreground)]">{data.document.id}</span>
              </div>
              <div className="grid grid-cols-3 p-3">
                <span className="text-[var(--muted)]">Created Date</span>
                <span className="col-span-2 text-[var(--foreground)]">
                  {new Date(data.document.createdAt).toLocaleString()}
                </span>
              </div>
              <div className="grid grid-cols-3 p-3">
                <span className="text-[var(--muted)]">Updated Date</span>
                <span className="col-span-2 text-[var(--foreground)]">
                  {new Date(data.document.updatedAt).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        )}

        {activeTab === "processing" && (
          <div className="space-y-4">
            <div>
              <h2 className="text-base font-semibold text-[var(--foreground)]">
                Processing Summary
              </h2>
              <p className="text-sm text-[var(--muted)] mt-0.5">
                Execution status across pipeline indexing stages.
              </p>
            </div>

            <div className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-[var(--muted)]">Overall Pipeline Status</span>
                <DocumentStatusBadge status={data.document.status} />
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-[var(--muted)]">Completed Stages</span>
                <span className="font-semibold tabular-nums text-[var(--foreground)]">
                  {data.processingSummary?.completedStages ?? "—"} / {data.processingSummary?.totalStages ?? "—"}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
