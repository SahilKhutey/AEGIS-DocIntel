"use client";

import React from "react";
import { DocumentLibrary } from "@/features/documents/components/document-library";

export default function DocumentsPage() {
  return (
    <div className="space-y-6">
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[var(--border)] pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
            Documents
          </h1>
          <h2 className="text-sm font-medium text-[var(--muted)] mt-1">
            Document Workspace &amp; Library
          </h2>
          <p className="text-xs text-[var(--muted)] mt-0.5">
            Ingest, inspect, explore documents and track indexing pipelines.
          </p>
        </div>
      </header>

      <DocumentLibrary />
    </div>
  );
}
