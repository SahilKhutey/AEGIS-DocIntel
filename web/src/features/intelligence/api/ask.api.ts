import { apiRequest } from "@/lib/api-client";
import { AnswerSchema, type AnswerResult } from "@/lib/schemas";
import { askResponseSchema, type AskResponse } from "../schemas/ask.schema";
import type { AskRequest, CitationReference } from "../types";

export async function askAegis(
  payload: AskRequest,
  signal?: AbortSignal,
): Promise<AskResponse> {
  const requestBody = {
    question: payload.question,
    document_ids: payload.documentIds && payload.documentIds.length > 0 ? payload.documentIds : [],
    conversation_id: payload.conversationId,
  };

  const raw = await apiRequest<AnswerResult>(
    "/api/v1/ask",
    AnswerSchema,
    {
      method: "POST",
      body: JSON.stringify(requestBody),
      signal,
    },
  );

  // Normalize citations from backend into standard CitationReference domain model
  const citations: CitationReference[] = (raw.citations || []).map((c, i) => {
    const matchingEv = (raw.evidence || []).find((e) => e.evidence_id === c.evidence_id);
    return {
      citationId: c.evidence_id || `cit-${i + 1}`,
      documentId: c.document_id,
      documentName: c.document_id,
      pageNumber: c.page_number ?? undefined,
      section: c.section_path?.join(" > ") || undefined,
      quote: matchingEv?.quote || raw.warnings?.[i] || undefined,
    };
  });

  const domainResponse: AskResponse = {
    answer: raw.answer,
    conversationId: payload.conversationId || raw.request_id,
    citations,
    warnings: raw.warnings || [],
    claims: citations.map((c) => ({
      claimId: `claim-${c.citationId}`,
      text: c.quote || `Supporting reference from ${c.documentId}`,
      citationIds: [c.citationId],
      supportStatus: raw.insufficient_evidence ? "unsupported" : "supported",
    })),
  };

  return askResponseSchema.parse(domainResponse);
}
