"use client";

import React from "react";
import type { RetrievalResult as Result } from "../types";

type Props = {
  result: Result;
  onOpenEvidence: (passageId: string, documentId: string) => void;
};

export function RetrievalResult({ result, onOpenEvidence }: Props) {
  return (
    <article className="rounded-xl border border-gray-200 bg-white p-5 shadow-xs space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-gray-100">
        <div className="flex items-center gap-2">
          {result.rank && (
            <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs font-semibold text-gray-700">
              #{result.rank}
            </span>
          )}
          <h3 className="font-semibold text-gray-900 text-sm">{result.documentName}</h3>
        </div>
        {result.pageNumber && (
          <span className="text-xs text-gray-500 font-medium">
            Page {result.pageNumber}
          </span>
        )}
      </div>

      {result.section && (
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
          {result.section}
        </p>
      )}

      <p className="my-2 whitespace-pre-wrap text-sm text-gray-800 leading-relaxed font-sans bg-gray-50/50 p-3 rounded-lg border border-gray-100">
        {result.text}
      </p>

      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-gray-100 text-xs">
        {result.score !== undefined ? (
          <p className="text-xs text-gray-500">
            Backend relevance score: <span className="font-mono font-medium text-gray-700">{result.score}</span>
          </p>
        ) : (
          <span />
        )}

        <button
          type="button"
          onClick={() => onOpenEvidence(result.passageId, result.documentId)}
          className="text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline"
        >
          Inspect evidence &rarr;
        </button>
      </div>
    </article>
  );
}
