"use client";

import React, { useState, useRef } from "react";
import { X, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { UploadDropzone } from "./upload-dropzone";
import { UploadProgress } from "./upload-progress";
import { validateUploadFile } from "../upload-validation";
import { DEFAULT_UPLOAD_POLICY, type UploadItem } from "../types";
import { defaultUploadService } from "../api";
import type { DocumentItem } from "@/lib/schemas";

export interface UploadDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (document: DocumentItem) => void;
}

export function UploadDialog({ isOpen, onClose, onSuccess }: UploadDialogProps) {
  const [items, setItems] = useState<UploadItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  if (!isOpen) return null;

  function handleFilesSelected(files: File[]) {
    setGlobalError(null);
    const newItems: UploadItem[] = files.map((file) => {
      const validation = validateUploadFile(file, DEFAULT_UPLOAD_POLICY);
      return {
        id: `${file.name}-${file.size}-${Date.now()}-${Math.random()}`,
        file,
        state: validation.valid ? "queued" : "failed",
        progress: 0,
        error: validation.valid ? undefined : validation.reason,
      };
    });
    setItems((prev) => [...prev, ...newItems]);
  }

  function handleRemoveItem(id: string) {
    if (uploading) return;
    setItems((prev) => prev.filter((item) => item.id !== id));
  }

  async function handleStartUpload() {
    const validItems = items.filter((item) => item.state === "queued" || item.state === "failed");
    if (validItems.length === 0) {
      setGlobalError("Please select at least one valid file to upload.");
      return;
    }

    setUploading(true);
    setGlobalError(null);
    abortControllerRef.current = new AbortController();

    let lastUploadedDoc: DocumentItem | null = null;

    for (const item of validItems) {
      try {
        setItems((prev) =>
          prev.map((i) => (i.id === item.id ? { ...i, state: "uploading", progress: 25 } : i))
        );

        const result = await defaultUploadService.upload(item.file, {
          signal: abortControllerRef.current.signal,
          onProgress: (p) => {
            setItems((prev) =>
              prev.map((i) => (i.id === item.id ? { ...i, progress: p } : i))
            );
          },
        });

        lastUploadedDoc = result.document;

        setItems((prev) =>
          prev.map((i) =>
            i.id === item.id
              ? {
                  ...i,
                  state: "uploaded",
                  progress: 100,
                  documentId: result.documentId,
                }
              : i
          )
        );
      } catch (err) {
        const message = err instanceof Error ? err.message : "Upload failed";
        setItems((prev) =>
          prev.map((i) =>
            i.id === item.id ? { ...i, state: "failed", error: message } : i
          )
        );
      }
    }

    setUploading(false);

    if (lastUploadedDoc && onSuccess) {
      onSuccess(lastUploadedDoc);
    }
  }

  function handleClose() {
    if (uploading) {
      if (confirm("An upload is in progress. Are you sure you want to cancel?")) {
        abortControllerRef.current?.abort();
        setUploading(false);
        onClose();
      }
      return;
    }
    setItems([]);
    setGlobalError(null);
    onClose();
  }

  const allCompleted = items.length > 0 && items.every((i) => i.state === "uploaded");

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="upload-dialog-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4"
    >
      <div className="w-full max-w-lg rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
          <div>
            <h2 id="upload-dialog-title" className="text-lg font-semibold text-[var(--foreground)]">
              Upload Documents
            </h2>
            <p className="text-xs text-[var(--muted)] mt-0.5">
              Submit files for ingestion, text extraction, and indexing.
            </p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="rounded-lg p-1 text-[var(--muted)] hover:bg-[var(--surface-muted)] hover:text-[var(--foreground)]"
            aria-label="Close modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {globalError && (
          <div role="alert" className="flex items-center gap-2 rounded-lg border border-red-300 bg-red-50 p-3 text-xs text-red-800">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{globalError}</span>
          </div>
        )}

        <UploadDropzone
          disabled={uploading}
          onFilesSelected={handleFilesSelected}
        />

        <div className="text-xs text-[var(--muted)] space-y-1">
          <p>Supported formats: PDF, DOCX, PPTX, HTML, TXT (Max 200 MB per file)</p>
          <p>Files are verified and scanned upon arrival.</p>
        </div>

        {items.length > 0 && (
          <div className="space-y-2 pt-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
              Selected files ({items.length})
            </h3>
            <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
              {items.map((item) => (
                <div key={item.id} className="relative">
                  <UploadProgress
                    fileName={item.file.name}
                    progress={item.progress}
                    state={
                      item.error
                        ? `Failed: ${item.error}`
                        : item.state === "uploaded"
                        ? "Completed"
                        : item.state === "uploading"
                        ? "Uploading..."
                        : "Ready to upload"
                    }
                  />
                  {!uploading && item.state !== "uploaded" && (
                    <button
                      type="button"
                      onClick={() => handleRemoveItem(item.id)}
                      className="absolute top-3 right-3 text-xs text-[var(--muted)] hover:text-red-600"
                      aria-label={`Remove ${item.file.name}`}
                    >
                      &times;
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex items-center justify-end gap-3 border-t border-[var(--border)] pt-4">
          <Button
            type="button"
            variant="outline"
            disabled={uploading}
            onClick={handleClose}
          >
            {allCompleted ? "Done" : "Cancel"}
          </Button>

          {!allCompleted && (
            <Button
              type="button"
              disabled={uploading || items.length === 0 || !items.some((i) => i.state !== "uploaded" && !i.error)}
              onClick={handleStartUpload}
            >
              {uploading ? "Uploading..." : "Start Upload"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
