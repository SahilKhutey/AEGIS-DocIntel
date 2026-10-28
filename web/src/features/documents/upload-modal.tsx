"use client";

import React, { useState, useRef } from "react";
import { DocumentSchema, type DocumentItem } from "@/lib/schemas";
import { apiRequest } from "@/lib/api-client";
import { ApiError } from "@/lib/errors";

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (document: DocumentItem) => void;
}

export function UploadModal({ isOpen, onClose, onSuccess }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setError("Please select a document file to upload.");
      return;
    }

    try {
      setUploading(true);
      setError(null);

      const formData = new FormData();
      formData.append("file", file);

      // POST to /api/v1/documents
      const doc = await apiRequest("/api/v1/documents", DocumentSchema, {
        method: "POST",
        body: formData,
      });

      onSuccess(doc);
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to upload document. Please retry.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="upload-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4"
    >
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-gray-100">
        <div className="flex items-center justify-between pb-3 border-b border-gray-100">
          <h2 id="upload-modal-title" className="text-lg font-semibold text-gray-900">
            Upload Document
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-lg p-1"
            aria-label="Close modal"
          >
            &times;
          </button>
        </div>

        <form onSubmit={handleUpload} className="mt-4 space-y-4">
          <div
            onClick={() => fileInputRef.current?.click()}
            className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 bg-gray-50/50 p-6 text-center cursor-pointer hover:border-blue-500 hover:bg-blue-50/20 transition"
          >
            <svg
              className="h-10 w-10 text-gray-400 mb-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className="text-sm font-medium text-gray-700">
              {file ? file.name : "Click to select or drag and drop document"}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Supported formats: PDF, DOCX, PPTX, HTML, TXT (Max 200MB)
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.pptx,.html,.txt,application/pdf,text/plain,text/html"
              className="hidden"
              onChange={(e) => {
                const selected = e.target.files?.[0];
                if (selected) setFile(selected);
              }}
            />
          </div>

          {error && (
            <div role="alert" className="rounded-lg bg-rose-50 p-3 text-xs text-rose-800">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={uploading}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading || !file}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 disabled:opacity-50"
            >
              {uploading ? "Uploading & Ingesting..." : "Upload Document"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
