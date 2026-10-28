"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { DocumentListSchema, type DocumentItem } from "@/lib/schemas";
import { apiRequest } from "@/lib/api-client";
import { ApiError } from "@/lib/errors";
import { StatusBadge } from "@/components/status-badge";
import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";
import { UploadModal } from "@/features/documents/upload-modal";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [requestId, setRequestId] = useState<string | undefined>();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  async function loadDocuments() {
    try {
      setLoading(true);
      setError(null);
      const data = await apiRequest("/api/v1/documents", DocumentListSchema);
      setDocuments(data.items || []);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        setRequestId(err.requestId);
      } else {
        setError("Unable to load documents. Please check backend connection.");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      const matchesSearch = doc.filename.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === "all" || doc.status.toLowerCase() === statusFilter.toLowerCase();
      return matchesSearch && matchesStatus;
    });
  }, [documents, searchQuery, statusFilter]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">
            Document Workspace
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Ingest, inspect, and explore documents and indexing pipelines.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={loadDocuments}
            className="inline-flex items-center rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-xs hover:bg-gray-50"
            title="Refresh document list"
          >
            Refresh
          </button>
          <button
            type="button"
            onClick={() => setIsUploadOpen(true)}
            className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-xs hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
          >
            Upload Document
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
        <div className="flex-1">
          <label htmlFor="doc-search" className="sr-only">
            Search documents
          </label>
          <input
            id="doc-search"
            type="text"
            placeholder="Search documents by filename..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3.5 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <div className="sm:w-48">
          <label htmlFor="status-filter" className="sr-only">
            Filter by status
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
          >
            <option value="all">All Statuses</option>
            <option value="ready">Ready</option>
            <option value="indexing">Indexing</option>
            <option value="pending">Pending</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="rounded-xl border border-gray-200 bg-white p-12 text-center" aria-busy="true">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" />
          <p className="mt-4 text-sm font-medium text-gray-600">Loading documents from tenant store...</p>
        </div>
      ) : error ? (
        <ErrorState
          title="Error Loading Documents"
          message={error}
          requestId={requestId}
          onRetry={loadDocuments}
        />
      ) : documents.length === 0 ? (
        <EmptyState
          title="No documents yet"
          description="Upload your first document to extract evidence, ask questions, and review facts."
          actionText="Upload Document"
          onAction={() => setIsUploadOpen(true)}
        />
      ) : filteredDocuments.length === 0 ? (
        <div className="rounded-xl border border-gray-200 bg-white p-8 text-center text-sm text-gray-500">
          No documents match your filter criteria.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xs">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
              <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wider text-gray-500">
                <tr>
                  <th scope="col" className="px-6 py-3.5">Filename</th>
                  <th scope="col" className="px-6 py-3.5">Status</th>
                  <th scope="col" className="px-6 py-3.5">Pages</th>
                  <th scope="col" className="px-6 py-3.5">Chunks</th>
                  <th scope="col" className="px-6 py-3.5">Ingested</th>
                  <th scope="col" className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {filteredDocuments.map((doc) => (
                  <tr key={doc.doc_id} className="hover:bg-gray-50/75 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900 max-w-xs truncate">
                      <Link
                        href={`/documents/${encodeURIComponent(doc.doc_id)}`}
                        className="text-blue-600 hover:text-blue-800 hover:underline"
                      >
                        {doc.filename}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={doc.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                      {doc.page_count != null ? doc.page_count : "—"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                      {doc.chunk_count != null ? doc.chunk_count : "—"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-500 text-xs font-mono">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right space-x-2">
                      <Link
                        href={`/documents/${encodeURIComponent(doc.doc_id)}`}
                        className="inline-flex items-center text-xs font-medium text-gray-700 hover:text-blue-600 bg-gray-100 px-2.5 py-1.5 rounded"
                      >
                        Inspect
                      </Link>
                      <Link
                        href={`/ask?doc_id=${encodeURIComponent(doc.doc_id)}`}
                        className="inline-flex items-center text-xs font-medium text-blue-700 hover:text-blue-900 bg-blue-50 px-2.5 py-1.5 rounded"
                      >
                        Ask
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={(newDoc) => {
          setDocuments((prev) => [newDoc, ...prev]);
        }}
      />
    </div>
  );
}
