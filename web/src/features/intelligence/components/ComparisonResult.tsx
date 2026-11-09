"use client";

import React from "react";
import type { ComparisonResponse } from "../types";
import { StatusBadge } from "@/components/status-badge";

type Props = {
  result: ComparisonResponse;
  onOpenDocument: (documentId: string) => void;
};

export function ComparisonResult({ result, onOpenDocument }: Props) {
  return (
    <section className="space-y-6" aria-label="Comparison Results">
      {result.summary && (
        <div className="rounded-2xl border border-blue-200 bg-blue-50/50 p-5 shadow-xs">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-blue-900 mb-1">
            Comparison Summary
          </h2>
          <p className="text-sm text-blue-950 font-medium">{result.summary}</p>
        </div>
      )}

      <div className="space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-700">
          Detected Differences &amp; Discrepancies ({result.differences.length})
        </h3>

        {result.differences.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-500 rounded-xl border border-dashed bg-gray-50">
            No conflicting facts or variations detected across the selected documents.
          </div>
        ) : (
          <div className="space-y-3">
            {result.differences.map((diff) => {
              const status =
                diff.significance === "high"
                  ? "conflict"
                  : diff.significance === "medium"
                    ? "warning"
                    : "ready";

              return (
                <article
                  key={diff.differenceId}
                  className="rounded-xl border border-gray-200 bg-white p-5 shadow-xs space-y-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-gray-100">
                    <h4 className="font-semibold text-gray-900 text-sm">{diff.category}</h4>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-400 capitalize">
                        Significance: {diff.significance ?? "unknown"}
                      </span>
                      <StatusBadge status={status} size="sm" />
                    </div>
                  </div>

                  <p className="text-sm text-gray-800 leading-relaxed">{diff.description}</p>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                    {diff.leftEvidence && (
                      <div className="rounded-lg bg-gray-50 border border-gray-100 p-3 text-xs space-y-1">
                        <span className="font-semibold text-gray-700 block">Document A Evidence</span>
                        <p className="text-gray-500 font-medium truncate">{diff.leftEvidence.documentName}</p>
                        {diff.leftEvidence.quote && (
                          <blockquote className="italic border-l-2 border-blue-400 pl-2 text-gray-700">
                            &ldquo;{diff.leftEvidence.quote}&rdquo;
                          </blockquote>
                        )}
                        <button
                          type="button"
                          onClick={() => onOpenDocument(diff.leftEvidence!.documentId)}
                          className="text-blue-600 hover:underline font-semibold block pt-1"
                        >
                          Open Document A &rarr;
                        </button>
                      </div>
                    )}

                    {diff.rightEvidence && (
                      <div className="rounded-lg bg-gray-50 border border-gray-100 p-3 text-xs space-y-1">
                        <span className="font-semibold text-gray-700 block">Document B Evidence</span>
                        <p className="text-gray-500 font-medium truncate">{diff.rightEvidence.documentName}</p>
                        {diff.rightEvidence.quote && (
                          <blockquote className="italic border-l-2 border-blue-400 pl-2 text-gray-700">
                            &ldquo;{diff.rightEvidence.quote}&rdquo;
                          </blockquote>
                        )}
                        <button
                          type="button"
                          onClick={() => onOpenDocument(diff.rightEvidence!.documentId)}
                          className="text-blue-600 hover:underline font-semibold block pt-1"
                        >
                          Open Document B &rarr;
                        </button>
                      </div>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
