"use client";

import React from "react";
import type { CitationReference } from "../types";

type Props = {
  citations: CitationReference[];
  activeCitationId?: string | null;
  onSelectCitation?: (citation: CitationReference) => void;
  brokenReferences?: string[];
};

export function CitationList({
  citations,
  activeCitationId,
  onSelectCitation,
  brokenReferences = [],
}: Props) {
  if (citations.length === 0) {
    return null;
  }

  const brokenSet = new Set(brokenReferences);

  return (
    <div className="space-y-3" aria-label="Citations and evidence references">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500">
          Source Citations ({citations.length})
        </h4>
        {brokenReferences.length > 0 && (
          <span className="inline-flex items-center rounded-full bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-800">
            {brokenReferences.length} Unresolved Reference{brokenReferences.length > 1 ? "s" : ""}
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {citations.map((cite, idx) => {
          const isSelected = activeCitationId === cite.citationId;
          const isBroken = brokenSet.has(cite.citationId);

          return (
            <button
              key={`${cite.citationId}-${idx}`}
              type="button"
              onClick={() => onSelectCitation?.(cite)}
              aria-label={`Citation ${idx + 1}: ${cite.documentName}${cite.pageNumber ? `, page ${cite.pageNumber}` : ""}`}
              className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium border transition ${
                isBroken
                  ? "border-rose-400 bg-rose-50 text-rose-900"
                  : isSelected
                    ? "bg-blue-100 text-blue-900 border-blue-400 font-semibold shadow-xs"
                    : "bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100"
              }`}
            >
              <span className="font-mono font-semibold">[{idx + 1}]</span>
              <span className="truncate max-w-[130px]">{cite.documentName || cite.documentId}</span>
              {cite.pageNumber && (
                <span className="text-gray-400 text-[11px]">p.{cite.pageNumber}</span>
              )}
              {isBroken && (
                <span className="ml-1 text-rose-600 font-bold" title="Unresolved citation">
                  !
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
