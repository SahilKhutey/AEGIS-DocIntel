import React from "react";
import Link from "next/link";
import { FileText, ArrowRight } from "lucide-react";
import type { DocumentRecord } from "@/features/documents/types";
import { DocumentStatusBadge } from "@/features/documents/components/document-status";

export type RecentDocumentsProps = {
  documents: DocumentRecord[];
};

export function RecentDocuments({ documents }: RecentDocumentsProps) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xs">
      <div className="flex items-center justify-between pb-4 border-b border-[var(--border)]">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-[var(--primary)]" />
          <h2 className="text-base font-semibold text-[var(--foreground)]">
            Recent Documents
          </h2>
        </div>
        <Link
          href="/documents"
          className="inline-flex items-center text-xs font-semibold text-[var(--primary)] hover:underline"
        >
          View library <ArrowRight className="ml-1 h-3.5 w-3.5" />
        </Link>
      </div>

      <div className="mt-4">
        {documents.length === 0 ? (
          <p className="text-sm text-[var(--muted)] py-4 text-center">
            No documents in this workspace yet.
          </p>
        ) : (
          <ul className="divide-y divide-[var(--border)]">
            {documents.slice(0, 4).map((doc) => (
              <li key={doc.id} className="py-3 flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <Link
                    href={`/documents/${encodeURIComponent(doc.id)}`}
                    className="text-sm font-medium text-[var(--foreground)] hover:text-[var(--primary)] hover:underline truncate block"
                  >
                    {doc.name}
                  </Link>
                  <p className="text-xs text-[var(--muted)] mt-0.5">
                    {doc.mimeType.split("/")[1]?.toUpperCase() || "DOCUMENT"} &middot;{" "}
                    {(doc.sizeBytes / 1024 / 1024).toFixed(1)} MB &middot;{" "}
                    {new Date(doc.updatedAt).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <DocumentStatusBadge status={doc.status} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
