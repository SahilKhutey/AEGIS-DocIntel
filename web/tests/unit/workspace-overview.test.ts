import { describe, expect, it } from "vitest";
import { fetchWorkspaceOverview } from "@/features/workspace-overview/api";
import type { DocumentService } from "@/features/documents/api";
import type { ProcessingService } from "@/features/processing/api";
import type { DocumentRecord, DocumentInspection } from "@/features/documents/types";
import type { ProcessingJob } from "@/features/processing/types";

describe("fetchWorkspaceOverview", () => {
  it("aggregates document statuses and active jobs into metrics", async () => {
    const mockDocuments: DocumentRecord[] = [
      {
        id: "doc-1",
        name: "Report1.pdf",
        mimeType: "application/pdf",
        sizeBytes: 1000000,
        status: "completed",
        createdAt: "2026-11-01T10:00:00Z",
        updatedAt: "2026-11-01T10:05:00Z",
      },
      {
        id: "doc-2",
        name: "Report2.pdf",
        mimeType: "application/pdf",
        sizeBytes: 2000000,
        status: "processing",
        createdAt: "2026-11-02T10:00:00Z",
        updatedAt: "2026-11-02T10:05:00Z",
      },
      {
        id: "doc-3",
        name: "FailedDoc.docx",
        mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        sizeBytes: 500000,
        status: "failed",
        createdAt: "2026-11-03T10:00:00Z",
        updatedAt: "2026-11-03T10:05:00Z",
      },
      {
        id: "doc-4",
        name: "PendingDoc.txt",
        mimeType: "text/plain",
        sizeBytes: 10000,
        status: "queued",
        createdAt: "2026-11-04T10:00:00Z",
        updatedAt: "2026-11-04T10:05:00Z",
      },
    ];

    const mockJobs: ProcessingJob[] = [
      {
        id: "job-1",
        tenantId: "default",
        jobType: "index_document",
        documentId: "doc-2",
        status: "running",
        progressPercent: 45,
        attempt: 1,
        maxAttempts: 3,
        createdAt: "2026-11-02T10:00:00Z",
        updatedAt: "2026-11-02T10:05:00Z",
      },
      {
        id: "job-2",
        tenantId: "default",
        jobType: "index_document",
        documentId: "doc-3",
        status: "failed",
        progressPercent: 30,
        attempt: 3,
        maxAttempts: 3,
        errorMessage: "Layout parse error",
        createdAt: "2026-11-03T10:00:00Z",
        updatedAt: "2026-11-03T10:05:00Z",
      },
    ];

    const mockDocService: DocumentService = {
      list: async () => ({ items: mockDocuments, total: 4 }),
      getById: async () => mockDocuments[0],
      delete: async () => {},
      reindex: async () => {},
      getInspection: async () => ({} as unknown as DocumentInspection),
    };

    const mockProcService: ProcessingService = {
      list: async () => ({ items: mockJobs, total: 2 }),
      getById: async () => mockJobs[0],
      retry: async () => {},
      cancel: async () => {},
    };

    const overview = await fetchWorkspaceOverview(mockDocService, mockProcService);

    expect(overview.metrics.totalDocuments).toBe(4);
    expect(overview.metrics.completedDocuments).toBe(1);
    expect(overview.metrics.processingDocuments).toBe(1);
    expect(overview.metrics.failedDocuments).toBe(1);
    expect(overview.metrics.queuedDocuments).toBe(1);
    expect(overview.metrics.activeJobs).toBe(1); // 1 running job
    expect(overview.metrics.attentionCount).toBe(2); // 1 failed doc + 1 failed job

    expect(overview.attentionItems).toHaveLength(2);
    expect(overview.attentionItems[0].id).toBe("doc-doc-3");
    expect(overview.attentionItems[1].id).toBe("job-job-2");
  });

  it("handles empty workspace gracefully", async () => {
    const mockDocService: DocumentService = {
      list: async () => ({ items: [], total: 0 }),
      getById: async () => {
        throw new Error("Not found");
      },
      delete: async () => {},
      reindex: async () => {},
      getInspection: async () => ({} as unknown as DocumentInspection),
    };

    const mockProcService: ProcessingService = {
      list: async () => ({ items: [], total: 0 }),
      getById: async () => {
        throw new Error("Not found");
      },
      retry: async () => {},
      cancel: async () => {},
    };

    const overview = await fetchWorkspaceOverview(mockDocService, mockProcService);

    expect(overview.metrics.totalDocuments).toBe(0);
    expect(overview.metrics.processingDocuments).toBe(0);
    expect(overview.metrics.completedDocuments).toBe(0);
    expect(overview.metrics.failedDocuments).toBe(0);
    expect(overview.metrics.queuedDocuments).toBe(0);
    expect(overview.metrics.activeJobs).toBe(0);
    expect(overview.metrics.attentionCount).toBe(0);
    expect(overview.attentionItems).toHaveLength(0);
  });
});
