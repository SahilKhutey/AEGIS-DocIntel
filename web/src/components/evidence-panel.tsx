import React from "react";
import type { Evidence } from "@/lib/schemas";

type EvidencePanelProps = {
  evidence: Evidence[];
  onOpenSource?: (item: Evidence) => void;
};

export function EvidencePanel({ evidence, onOpenSource }: EvidencePanelProps) {
  if (evidence.length === 0) {
    return (
      <section aria-label="Evidence" className="rounded-xl border border-gray-200 bg-white p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-500 mb-2">
          Evidence
        </h2>
        <p className="text-sm text-gray-500 italic">
          No supporting evidence was returned for this answer.
        </p>
      </section>
    );
  }

  return (
    <section aria-label="Evidence" className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-gray-100 mb-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-700">
          Supporting Evidence ({evidence.length})
        </h2>
        <span className="text-xs text-gray-500">Verified ground passages</span>
      </div>
      <ol className="space-y-4">
        {evidence.map((item, index) => {
          const key = `${item.document_id}:${item.chunk_id || index}`;
          return (
            <li
              key={key}
              className="rounded-lg border border-gray-100 bg-gray-50/60 p-4 transition-colors hover:bg-gray-50"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className="inline-flex items-center rounded-md bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                  Source {index + 1}
                </span>
                <span className="text-xs font-mono text-gray-400 truncate max-w-[180px]">
                  {item.chunk_id || item.document_id}
                </span>
              </div>
              <blockquote className="text-sm text-gray-800 border-l-2 border-blue-500 pl-3 my-2 italic">
                &ldquo;{item.quote || "Evidence passage quote unavailable."}&rdquo;
              </blockquote>
              <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-gray-200/60 text-xs text-gray-500">
                <p>
                  {item.page_number != null ? `Page ${item.page_number}` : "Page not provided"}
                  {item.section_path?.length ? ` · ${item.section_path.join(" / ")}` : ""}
                </p>
                {onOpenSource && (
                  <button
                    type="button"
                    onClick={() => onOpenSource(item)}
                    aria-label={`Open source ${index + 1}`}
                    className="font-medium text-blue-600 hover:text-blue-800 hover:underline"
                  >
                    Open source &rarr;
                  </button>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
