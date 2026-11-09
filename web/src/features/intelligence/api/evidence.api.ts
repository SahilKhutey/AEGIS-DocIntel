import { apiRequest } from "@/lib/api-client";
import { DocumentChunkListSchema } from "@/lib/schemas";
import type { EvidenceRecord } from "../types";

export async function getDocumentEvidence(
  documentId: string,
  signal?: AbortSignal,
): Promise<EvidenceRecord[]> {
  try {
    const data = await apiRequest<{
      items?: Array<{
        chunk_id: string;
        doc_id: string;
        text: string;
        page_number?: number | null;
        section_title?: string | null;
      }>;
    }>(
      `/api/v1/documents/${encodeURIComponent(documentId)}/chunks`,
      DocumentChunkListSchema,
      { signal },
    );

    return (data.items || []).map((c) => ({
      evidenceId: c.chunk_id,
      documentId: c.doc_id,
      documentName: c.doc_id,
      passageId: c.chunk_id,
      pageNumber: c.page_number ?? undefined,
      section: c.section_title ?? undefined,
      content: c.text,
      evidenceType: "document_passage",
    }));
  } catch (err) {
    throw err;
  }
}
