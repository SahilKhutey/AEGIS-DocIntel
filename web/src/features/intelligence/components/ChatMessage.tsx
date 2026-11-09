"use client";

import React, { useState } from "react";
import type { AskResponse, CitationReference } from "../types";
import { CitationList } from "./CitationList";
import { validateAnswerCitations } from "../utils/citation-utils";
import { Copy, Check, AlertTriangle } from "lucide-react";

export type MessageRole = "user" | "assistant";

export type ChatMessageItem = {
  id: string;
  role: MessageRole;
  text: string;
  response?: AskResponse;
  timestamp: string;
};

type Props = {
  message: ChatMessageItem;
  onSelectCitation?: (citation: CitationReference) => void;
  activeCitationId?: string | null;
};

export function ChatMessage({
  message,
  onSelectCitation,
  activeCitationId,
}: Props) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    void navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-2xl rounded-2xl bg-blue-600 px-5 py-3 text-sm text-white shadow-xs">
          <p className="whitespace-pre-wrap">{message.text}</p>
          <span className="mt-1 block text-right text-[11px] text-blue-200">
            {message.timestamp}
          </span>
        </div>
      </div>
    );
  }

  const response = message.response;
  const validation = response
    ? validateAnswerCitations({
        claims: response.claims,
        citations: response.citations,
      })
    : { valid: true, brokenReferences: [] };

  const brokenIds = validation.brokenReferences.map((b) => b.citationId);

  return (
    <article
      className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs space-y-4"
      aria-label="AEGIS grounded answer"
    >
      <header className="flex items-center justify-between pb-3 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
            Grounded Answer
          </span>
          {response?.claims?.some((c) => c.supportStatus === "unsupported") ? (
            <span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800">
              Safe Abstention: Insufficient Evidence
            </span>
          ) : (
            <span className="inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800">
              Verified Grounded
            </span>
          )}
        </div>

        <button
          type="button"
          onClick={handleCopy}
          aria-label="Copy answer to clipboard"
          className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-2.5 py-1 text-xs font-medium text-gray-600 hover:bg-gray-50 transition"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 text-emerald-600" />
              <span>Copied</span>
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </header>

      {/* Answer content */}
      <div className="text-gray-900 leading-relaxed whitespace-pre-wrap text-base">
        {message.text}
      </div>

      {/* Citation integrity alert */}
      {!validation.valid && (
        <div
          role="alert"
          className="rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-xs text-rose-900 flex items-start gap-2.5"
        >
          <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Citation Integrity Warning:</span>{" "}
            Found {validation.brokenReferences.length} citation reference(s) that do not resolve to available source records.
          </div>
        </div>
      )}

      {/* Warnings / Source Inconsistencies */}
      {response?.warnings && response.warnings.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3.5 text-xs text-amber-900">
          <div className="font-semibold mb-1 flex items-center gap-1.5">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-700" />
            Source Inconsistency Warnings:
          </div>
          <ul className="list-disc pl-4 space-y-0.5">
            {response.warnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Citations List */}
      {response?.citations && response.citations.length > 0 && (
        <div className="pt-2 border-t border-gray-100">
          <CitationList
            citations={response.citations}
            activeCitationId={activeCitationId}
            onSelectCitation={onSelectCitation}
            brokenReferences={brokenIds}
          />
        </div>
      )}
    </article>
  );
}
