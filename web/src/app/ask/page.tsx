"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  DocumentListSchema,
  AnswerSchema,
  type DocumentItem,
  type AnswerResult,
  type Evidence,
} from "@/lib/schemas";
import { apiRequest } from "@/lib/api-client";
import { ApiError } from "@/lib/errors";
import { EvidencePanel } from "@/components/evidence-panel";
import { ErrorState } from "@/components/error-state";
import { QuestionComposer } from "@/features/intelligence/components/QuestionComposer";
import {
  ChatMessage,
  type ChatMessageItem,
} from "@/features/intelligence/components/ChatMessage";
import type { AskResponse, CitationReference } from "@/features/intelligence/types";

function AskContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialDocId = searchParams.get("doc_id") || "";

  const [selectedDocIds, setSelectedDocIds] = useState<string[]>(
    initialDocId ? [initialDocId] : [],
  );
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [answerResult, setAnswerResult] = useState<AnswerResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [docsLoading, setDocsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeCitationId, setActiveCitationId] = useState<string | null>(null);

  useEffect(() => {
    async function loadDocs() {
      try {
        setDocsLoading(true);
        const data = await apiRequest("/api/v1/documents", DocumentListSchema);
        setDocuments(data.items || []);
      } catch {
        // Continue even if document list fails to load
      } finally {
        setDocsLoading(false);
      }
    }
    loadDocs();
  }, []);

  async function handleAskQuestion(questionText: string) {
    if (!questionText.trim()) return;

    const userMessage: ChatMessageItem = {
      id: `msg-user-${Date.now()}`,
      role: "user",
      text: questionText.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setError(null);
    setActiveCitationId(null);

    try {
      const payload = {
        question: questionText.trim(),
        document_ids: selectedDocIds.length > 0 ? selectedDocIds : [],
      };

      const result = await apiRequest("/api/v1/ask", AnswerSchema, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setAnswerResult(result);

      // Construct normalized domain response
      const citations: CitationReference[] = (result.citations || []).map((c, i) => {
        const matchingEv = (result.evidence || []).find((e) => e.evidence_id === c.evidence_id);
        return {
          citationId: c.evidence_id || `cit-${i + 1}`,
          documentId: c.document_id,
          documentName: c.document_id,
          pageNumber: c.page_number ?? undefined,
          section: c.section_path?.join(" > ") || undefined,
          quote: matchingEv?.quote || result.warnings?.[i] || undefined,
        };
      });

      const domainResponse: AskResponse = {
        answer: result.answer,
        conversationId: result.request_id,
        citations,
        warnings: result.warnings || [],
        claims: citations.map((c) => ({
          claimId: `claim-${c.citationId}`,
          text: c.quote || `Supporting reference from ${c.documentId}`,
          citationIds: [c.citationId],
          supportStatus: result.insufficient_evidence ? "unsupported" : "supported",
        })),
      };

      const assistantMessage: ChatMessageItem = {
        id: `msg-assistant-${Date.now()}`,
        role: "assistant",
        text: result.answer,
        response: domainResponse,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to obtain grounded answer.");
    } finally {
      setLoading(false);
    }
  }

  // Synthesize evidence items from citations + evidence array for the persistent evidence panel
  const displayEvidence: Evidence[] = (answerResult?.evidence && answerResult.evidence.length > 0)
    ? answerResult.evidence
    : (answerResult?.citations || []).map((c, i) => ({
        document_id: c.document_id,
        chunk_id: c.evidence_id,
        quote: answerResult?.warnings?.[i] || "Cited source passage",
        page_number: c.page_number,
        section_path: c.section_path,
      }));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Ask AEGIS
        </h1>
        <h2 className="sr-only">Ask &amp; Evidence Explorer</h2>
        <p className="text-sm text-gray-500 mt-1">
          <span className="font-medium text-gray-700">Ask &amp; Evidence Explorer</span> — Ask questions across authorized documents with strictly grounded citations and transparent abstention.
        </p>
      </div>

      {/* Document Scope Filter */}
      <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500">
            Document Scope ({selectedDocIds.length > 0 ? `${selectedDocIds.length} Selected` : "All Tenant Documents"})
          </label>
          {selectedDocIds.length > 0 && (
            <button
              type="button"
              onClick={() => setSelectedDocIds([])}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
            >
              Clear Scope Filter
            </button>
          )}
        </div>

        {docsLoading ? (
          <p className="text-xs text-gray-600">Loading authorized documents...</p>
        ) : documents.length === 0 ? (
          <p className="text-xs text-gray-500">Searching all tenant documents.</p>
        ) : (
          <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-1">
            {documents.map((d) => {
              const isSelected = selectedDocIds.includes(d.doc_id);
              return (
                <button
                  key={d.doc_id}
                  type="button"
                  onClick={() => {
                    setSelectedDocIds((prev) =>
                      isSelected ? prev.filter((id) => id !== d.doc_id) : [...prev, d.doc_id],
                    );
                  }}
                  className={`rounded-lg px-2.5 py-1 text-xs font-medium border transition ${
                    isSelected
                      ? "bg-blue-600 text-white border-blue-600 shadow-xs"
                      : "bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100"
                  }`}
                >
                  {d.filename} {isSelected ? "✓" : ""}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Query Form / Composer */}
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs">
        <QuestionComposer
          onSubmit={(q) => void handleAskQuestion(q)}
          isLoading={loading}
          submitLabel="Ask AEGIS (Ask Question)"
          placeholder="e.g., What is the aggregate liability cap under the agreement, and what exceptions apply?"
        />
      </div>

      {error && (
        <ErrorState
          title="Query Error"
          message={error}
          onRetry={() => {
            if (messages.length > 0) {
              const lastUser = [...messages].reverse().find((m) => m.role === "user");
              if (lastUser) void handleAskQuestion(lastUser.text);
            }
          }}
        />
      )}

      {/* Conversation & Evidence Display */}
      {(messages.length > 0 || answerResult) && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Main Conversation Column */}
          <div className="lg:col-span-2 space-y-4">
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                activeCitationId={activeCitationId}
                onSelectCitation={(cite) => {
                  setActiveCitationId(cite.citationId);
                }}
              />
            ))}
          </div>

          {/* Evidence Panel Column */}
          <div className="lg:col-span-1">
            <EvidencePanel
              evidence={displayEvidence}
              onOpenSource={(item) => {
                router.push(`/documents/${encodeURIComponent(item.document_id)}`);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default function AskPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gray-500">Loading Ask Workbench...</div>}>
      <AskContent />
    </Suspense>
  );
}
