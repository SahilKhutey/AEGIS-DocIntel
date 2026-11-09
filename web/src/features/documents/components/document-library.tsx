"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { Search, RefreshCw, Upload, FileText, AlertCircle } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { DocumentStatusBadge } from "./document-status";
import { defaultDocumentService } from "../api";
import { UploadDialog } from "@/features/uploads/components/upload-dialog";
import type {
  DocumentListResponse,
  DocumentStatus,
  DocumentRecord,
} from "../types";

type DocumentLibraryProps = {
  loadDocuments?: (input: {
    query: string;
    status?: DocumentStatus;
  }) => Promise<DocumentListResponse>;
  initialDocuments?: DocumentRecord[];
};

const statuses: Array<{
  label: string;
  value: DocumentStatus | "all";
}> = [
  { label: "All", value: "all" },
  { label: "Completed", value: "completed" },
  { label: "Processing", value: "processing" },
  { label: "Queued", value: "queued" },
  { label: "Failed", value: "failed" },
];

export function DocumentLibrary({
  loadDocuments,
  initialDocuments,
}: DocumentLibraryProps) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<DocumentStatus | "all">("all");
  const [data, setData] = useState<DocumentListResponse>({
    items: initialDocuments || [],
    total: initialDocuments?.length || 0,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      if (loadDocuments) {
        const response = await loadDocuments({
          query,
          status: status === "all" ? undefined : status,
        });
        setData(response);
      } else {
        const response = await defaultDocumentService.list({
          query,
          status: status === "all" ? undefined : status,
        });
        setData(response);
      }
    } catch {
      setError("Unable to load documents. Please check backend connection.");
    } finally {
      setLoading(false);
    }
  }, [loadDocuments, query, status]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const displayedItems = useMemo(() => {
    return data.items.filter((item) => {
      const matchesSearch =
        !query ||
        item.name.toLowerCase().includes(query.toLowerCase()) ||
        item.id.toLowerCase().includes(query.toLowerCase());
      const matchesStatus = status === "all" || item.status === status;
      return matchesSearch && matchesStatus;
    });
  }, [data.items, query, status]);

  return (
    <section className="space-y-5">
      {/* Search and Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="relative min-w-48 flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted)]" />
          <Input
            id="doc-search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search documents by filename..."
            aria-label="Search documents"
            className="pl-9"
          />
        </div>

        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            disabled={loading}
            onClick={() => void refresh()}
            title="Refresh document list"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>

          <Button
            type="button"
            onClick={() => setIsUploadOpen(true)}
          >
            <Upload className="mr-2 h-4 w-4" />
            Upload Document
          </Button>
        </div>
      </div>

      {/* Status Filter Badges */}
      <div
        className="flex flex-wrap gap-2"
        role="group"
        aria-label="Document status filters"
      >
        {statuses.map((item) => (
          <Button
            key={item.value}
            size="sm"
            variant={status === item.value ? "primary" : "outline"}
            aria-pressed={status === item.value}
            onClick={() => setStatus(item.value)}
          >
            {item.label}
          </Button>
        ))}
      </div>

      {/* Error Alert */}
      {error && (
        <div
          role="alert"
          className="flex items-center justify-between rounded-xl border border-red-300 bg-red-50 p-4 text-sm text-red-800"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 shrink-0 text-red-600" />
            <span>{error}</span>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => void refresh()}
          >
            Retry
          </Button>
        </div>
      )}

      {/* Content Area */}
      {loading ? (
        <div
          role="status"
          aria-live="polite"
          className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-12 text-center text-sm text-[var(--muted)]"
        >
          Loading documents…
        </div>
      ) : displayedItems.length === 0 ? (
        <div className="rounded-xl border-2 border-dashed border-[var(--border)] bg-[var(--surface)] p-12 text-center">
          <FileText className="mx-auto h-12 w-12 text-[var(--muted)] mb-3" />
          <h2 className="text-base font-semibold text-[var(--foreground)]">
            No documents found
          </h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Try another search or upload a new document to begin indexing.
          </p>
          <Button
            type="button"
            onClick={() => setIsUploadOpen(true)}
            className="mt-4"
          >
            <Upload className="mr-2 h-4 w-4" />
            Select File to Ingest
          </Button>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-xs">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-[var(--border)] bg-[var(--surface-muted)] text-xs font-semibold uppercase text-[var(--muted)]">
              <tr>
                <th scope="col" className="p-3.5">Document</th>
                <th scope="col" className="p-3.5">Type</th>
                <th scope="col" className="p-3.5">Size</th>
                <th scope="col" className="p-3.5">Status</th>
                <th scope="col" className="p-3.5">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {displayedItems.map((doc) => (
                <tr
                  key={doc.id}
                  className="hover:bg-[var(--surface-muted)] transition-colors"
                >
                  <td className="p-3.5">
                    <Link
                      href={`/documents/${encodeURIComponent(doc.id)}`}
                      className="font-medium text-[var(--primary)] hover:underline flex items-center gap-2"
                    >
                      <FileText className="h-4 w-4 shrink-0 text-[var(--muted)]" />
                      <span className="truncate max-w-xs sm:max-w-md">{doc.name}</span>
                    </Link>
                  </td>
                  <td className="p-3.5 text-xs text-[var(--muted)]">
                    {doc.mimeType.split("/")[1]?.toUpperCase() || doc.mimeType}
                  </td>
                  <td className="p-3.5 text-xs text-[var(--muted)] tabular-nums">
                    {(doc.sizeBytes / 1024 / 1024).toFixed(2)} MB
                  </td>
                  <td className="p-3.5">
                    <DocumentStatusBadge status={doc.status} />
                  </td>
                  <td className="p-3.5 text-xs text-[var(--muted)] tabular-nums">
                    {new Date(doc.updatedAt).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-[var(--muted)] pt-2">
        <span>
          Showing {displayedItems.length} of {data.total || displayedItems.length} documents
        </span>
      </div>

      <UploadDialog
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={() => {
          setIsUploadOpen(false);
          void refresh();
        }}
      />
    </section>
  );
}
