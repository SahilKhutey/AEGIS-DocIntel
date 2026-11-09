import { apiRequest } from "@/lib/api-client";
import { DocumentChunkListSchema } from "@/lib/schemas";
import { retrievalResponseSchema, type RetrievalResponse } from "../schemas/retrieval.schema";
import type { RetrievalRequest } from "../types";

export async function retrieveDocuments(
  payload: RetrievalRequest,
  signal?: AbortSignal,
): Promise<RetrievalResponse> {
  try {
    return await apiRequest<RetrievalResponse>(
      "/api/v1/retrieve",
      retrievalResponseSchema,
      {
        method: "POST",
        body: JSON.stringify(payload),
        signal,
      },
    );
  } catch (err) {
    // If dedicated retrieve endpoint is not yet deployed, fallback to retrieving scoped document chunks
    if (payload.documentIds && payload.documentIds.length > 0) {
      const docId = payload.documentIds[0];
      try {
        const chunksData = await apiRequest(
          `/api/v1/documents/${encodeURIComponent(docId)}/chunks`,
          DocumentChunkListSchema,
          { signal },
        );

        const queryLower = payload.query.toLowerCase();
        const filtered = (chunksData.items || []).filter((c) =>
          c.text.toLowerCase().includes(queryLower),
        );

        return {
          results: filtered.map((c, idx) => ({
            resultId: `ret-${c.chunk_id}`,
            documentId: c.doc_id,
            documentName: c.doc_id,
            passageId: c.chunk_id,
            pageNumber: c.page_number ?? undefined,
            section: c.section_title ?? undefined,
            text: c.text,
            score: 0.85,
            rank: idx + 1,
          })),
          total: filtered.length,
          page: 1,
          pageSize: 20,
        };
      } catch {
        // rethrow original error
      }
    }
    throw err;
  }
}
