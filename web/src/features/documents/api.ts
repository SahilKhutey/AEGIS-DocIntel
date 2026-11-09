import { apiRequest } from "@/lib/api-client";
import {
  DocumentSchema,
  DocumentListSchema,
  DocumentChunkListSchema,
  ExtractedFactSchema,
  type DocumentItem,
} from "@/lib/schemas";
import { z } from "zod";
import type {
  DocumentListQuery,
  DocumentListResponse,
  DocumentRecord,
  DocumentStatus,
  DocumentInspection,
  ExtractedTextPage,
} from "./types";

export function mapBackendStatusToDocumentStatus(status: string): DocumentStatus {
  switch (status.toLowerCase()) {
    case "ready":
      return "completed";
    case "indexing":
    case "reindexing":
      return "processing";
    case "pending":
      return "queued";
    case "failed":
      return "failed";
    case "uploaded":
      return "uploaded";
    case "cancelled":
      return "cancelled";
    default:
      return "queued";
  }
}

export function mapDocumentStatusToBackend(status?: DocumentStatus): string | undefined {
  if (!status) return undefined;
  switch (status) {
    case "completed":
      return "ready";
    case "processing":
      return "indexing";
    case "queued":
      return "pending";
    case "failed":
      return "failed";
    default:
      return undefined;
  }
}

function detectMimeType(filename: string): string {
  const lower = filename.toLowerCase();
  if (lower.endsWith(".pdf")) return "application/pdf";
  if (lower.endsWith(".docx"))
    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
  if (lower.endsWith(".pptx"))
    return "application/vnd.openxmlformats-officedocument.presentationml.presentation";
  if (lower.endsWith(".html") || lower.endsWith(".htm")) return "text/html";
  if (lower.endsWith(".xlsx"))
    return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
  return "text/plain";
}

export function mapBackendDocumentToRecord(doc: DocumentItem): DocumentRecord {
  return {
    id: doc.doc_id,
    name: doc.filename,
    mimeType: detectMimeType(doc.filename),
    sizeBytes: (doc.page_count || 1) * 250000,
    status: mapBackendStatusToDocumentStatus(doc.status),
    createdAt: doc.created_at,
    updatedAt: doc.indexed_at || doc.created_at,
    pageCount: doc.page_count ?? undefined,
    chunkCount: doc.chunk_count ?? undefined,
  };
}

export interface DocumentService {
  list(query?: DocumentListQuery): Promise<DocumentListResponse>;
  getById(id: string): Promise<DocumentRecord>;
  delete(id: string): Promise<void>;
  reindex(id: string): Promise<void>;
  getInspection(id: string): Promise<DocumentInspection>;
}

export class DefaultDocumentService implements DocumentService {
  async list(query?: DocumentListQuery): Promise<DocumentListResponse> {
    const params = new URLSearchParams();
    if (query?.page) params.set("page", String(query.page));
    if (query?.limit) params.set("page_size", String(query.limit));
    const backendStatus = mapDocumentStatusToBackend(query?.status);
    if (backendStatus) params.set("status", backendStatus);

    const path = `/api/v1/documents${params.toString() ? `?${params.toString()}` : ""}`;
    const response = await apiRequest(path, DocumentListSchema);

    let items = response.items.map(mapBackendDocumentToRecord);

    if (query?.query) {
      const q = query.query.toLowerCase();
      items = items.filter(
        (doc) => doc.name.toLowerCase().includes(q) || doc.id.toLowerCase().includes(q)
      );
    }

    if (query?.sortBy) {
      items.sort((a, b) => {
        const order = query.sortOrder === "desc" ? -1 : 1;
        if (query.sortBy === "name") return a.name.localeCompare(b.name) * order;
        if (query.sortBy === "sizeBytes") return (a.sizeBytes - b.sizeBytes) * order;
        return (new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()) * order;
      });
    }

    return {
      items,
      total: response.total || items.length,
      page: response.page,
      pageSize: response.page_size,
    };
  }

  async getById(id: string): Promise<DocumentRecord> {
    const encodedId = encodeURIComponent(id);
    const doc = await apiRequest(`/api/v1/documents/${encodedId}`, DocumentSchema);
    return mapBackendDocumentToRecord(doc);
  }

  async delete(id: string): Promise<void> {
    const encodedId = encodeURIComponent(id);
    await apiRequest(`/api/v1/documents/${encodedId}`, z.unknown(), {
      method: "DELETE",
    });
  }

  async reindex(id: string): Promise<void> {
    const encodedId = encodeURIComponent(id);
    await apiRequest(`/api/v1/documents/${encodedId}/reindex`, z.unknown(), {
      method: "POST",
    });
  }

  async getInspection(id: string): Promise<DocumentInspection> {
    const encodedId = encodeURIComponent(id);
    const doc = await this.getById(id);

    let extractedPages: ExtractedTextPage[] = [];
    try {
      const chunkData = await apiRequest(
        `/api/v1/documents/${encodedId}/chunks`,
        DocumentChunkListSchema
      );
      extractedPages = (chunkData.items || []).map((chunk, index) => ({
        pageNumber: chunk.page_number || index + 1,
        text: chunk.text,
        chunkId: chunk.chunk_id,
        sectionTitle: chunk.section_title || undefined,
      }));
    } catch {
      // Chunks are optional
    }

    try {
      await apiRequest(
        `/api/v1/documents/${encodedId}/facts`,
        z.object({ facts: z.array(ExtractedFactSchema) })
      );
    } catch {
      // Facts are optional
    }

    return {
      document: doc,
      metadata: {
        title: doc.name,
        pageCount: doc.pageCount,
        chunkCount: doc.chunkCount,
        createdAt: doc.createdAt,
        modifiedAt: doc.updatedAt,
      },
      extractedPages: extractedPages.length > 0 ? extractedPages : undefined,
      previewAvailable: doc.name.toLowerCase().endsWith(".pdf"),
      processingSummary: {
        status: doc.status,
        completedStages: doc.status === "completed" ? 6 : doc.status === "processing" ? 3 : 1,
        totalStages: 6,
      },
    };
  }
}

export const defaultDocumentService = new DefaultDocumentService();
