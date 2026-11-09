import React from "react";
import type { EvidenceRecord } from "../types";

type Props = {
  evidence: EvidenceRecord;
  onOpenDocument: (documentId: string) => void;
};

export function EvidenceDetail({ evidence, onOpenDocument }: Props) {
  return (
    <article className="space-y-3 rounded-xl border border-gray-200 bg-white p-5 shadow-xs">
      <header className="flex items-center justify-between pb-2 border-b border-gray-100">
        <div>
          <h3 className="font-semibold text-gray-900 text-sm">{evidence.documentName}</h3>
          <p className="text-xs text-gray-400 font-mono truncate max-w-[200px]">{evidence.evidenceId}</p>
        </div>
        <p className="text-xs text-gray-500 font-medium">
          {evidence.pageNumber ? `Page ${evidence.pageNumber}` : "Page reference unavailable"}
        </p>
      </header>

      {evidence.section && (
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          {evidence.section}
        </p>
      )}

      <blockquote className="border-l-2 border-blue-500 pl-4 py-1 text-sm italic text-gray-800 bg-gray-50/50 rounded-r leading-relaxed">
        &ldquo;{evidence.content}&rdquo;
      </blockquote>

      <div className="flex items-center justify-between pt-2 border-t border-gray-100">
        <span className="text-[11px] text-gray-400">
          {evidence.evidenceType ? `Type: ${evidence.evidenceType}` : "Verified source record"}
        </span>
        <button
          type="button"
          onClick={() => onOpenDocument(evidence.documentId)}
          className="text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline"
        >
          Open source document &rarr;
        </button>
      </div>
    </article>
  );
}
