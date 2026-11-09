"use client";

import React, { useState } from "react";
import { Check, Copy, ChevronDown, ChevronRight } from "lucide-react";

export interface JsonViewerProps {
  data: unknown;
  title?: string;
  initialExpanded?: boolean;
  maxHeight?: string;
  className?: string;
}

export const JsonViewer: React.FC<JsonViewerProps> = ({
  data,
  title = "Payload",
  initialExpanded = true,
  maxHeight = "400px",
  className = "",
}) => {
  const [isExpanded, setIsExpanded] = useState(initialExpanded);
  const [copied, setCopied] = useState(false);

  const formattedJson = typeof data === "string" ? data : JSON.stringify(data, null, 2);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(formattedJson);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  return (
    <div className={`rounded-lg border border-slate-200 bg-slate-900 text-slate-100 overflow-hidden ${className}`}>
      <div className="flex items-center justify-between px-3 py-2 bg-slate-800 border-b border-slate-700 text-xs font-mono">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1.5 font-medium text-slate-300 hover:text-white transition-colors cursor-pointer"
          aria-expanded={isExpanded}
        >
          {isExpanded ? (
            <ChevronDown className="w-3.5 h-3.5" aria-hidden="true" />
          ) : (
            <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
          )}
          <span>{title}</span>
        </button>
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs transition-colors cursor-pointer"
          aria-label="Copy JSON to clipboard"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" aria-hidden="true" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" aria-hidden="true" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {isExpanded && (
        <pre
          className="p-3 text-xs font-mono overflow-auto text-slate-200 leading-relaxed"
          style={{ maxHeight }}
        >
          <code>{formattedJson}</code>
        </pre>
      )}
    </div>
  );
};
