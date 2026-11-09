"use client";

import React, { useState } from "react";
import type { DocumentItem } from "@/lib/schemas";
import { Button } from "@/components/ui/button";

type Props = {
  documents: DocumentItem[];
  selectedDocIds: string[];
  onToggleDoc: (docId: string) => void;
  onCompare: (mode: "content" | "semantic" | "structured") => void;
  isLoading?: boolean;
};

export function ComparisonWorkspace({
  documents,
  selectedDocIds,
  onToggleDoc,
  onCompare,
  isLoading = false,
}: Props) {
  const [mode, setMode] = useState<"content" | "semantic" | "structured">("structured");

  const canCompare = selectedDocIds.length >= 2;

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-gray-100">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-700">
            Select Documents to Compare (min 2)
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Select at least two documents from your authorized tenant repository.
          </p>
        </div>
        <span className="inline-flex items-center rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700 border border-blue-200">
          Selected: {selectedDocIds.length}
        </span>
      </div>

      {/* Mode selection */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold uppercase text-gray-500 mr-2">
          Comparison Mode:
        </span>
        {(["structured", "semantic", "content"] as const).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            className={`rounded-lg px-2.5 py-1 text-xs font-medium capitalize border transition ${
              mode === m
                ? "bg-blue-600 text-white border-blue-600 shadow-xs"
                : "bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100"
            }`}
          >
            {m}
          </button>
        ))}
      </div>

      {/* Document cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
        {documents.map((d) => {
          const isSelected = selectedDocIds.includes(d.doc_id);
          return (
            <div
              key={d.doc_id}
              onClick={() => onToggleDoc(d.doc_id)}
              className={`rounded-xl border p-4 cursor-pointer transition flex items-center justify-between ${
                isSelected
                  ? "border-blue-500 bg-blue-50/40 text-blue-900 shadow-xs ring-1 ring-blue-500"
                  : "border-gray-200 bg-white hover:bg-gray-50 text-gray-800"
              }`}
            >
              <div className="truncate mr-2">
                <p className="text-sm font-semibold truncate">{d.filename}</p>
                <p className="text-xs text-gray-400 font-mono truncate">{d.doc_id}</p>
              </div>
              <span
                className={`h-5 w-5 rounded-md flex items-center justify-center text-xs font-bold shrink-0 ${
                  isSelected ? "bg-blue-600 text-white" : "border border-gray-300 text-transparent"
                }`}
              >
                ✓
              </span>
            </div>
          );
        })}
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
        {!canCompare && (
          <p className="text-xs text-amber-600 font-medium">
            Please select at least 2 documents to initiate comparison.
          </p>
        )}
        <div className="sm:ml-auto">
          <Button
            type="button"
            onClick={() => onCompare(mode)}
            disabled={!canCompare || isLoading}
            variant="primary"
            className="rounded-xl px-5 py-2.5 text-sm font-semibold"
          >
            {isLoading ? "Comparing Documents..." : "Compare Selected Documents"}
          </Button>
        </div>
      </div>
    </div>
  );
}
