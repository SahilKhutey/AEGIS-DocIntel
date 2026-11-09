import { apiRequest } from "@/lib/api-client";
import { JobListSchema, JobSchema, type JobItem } from "@/lib/schemas";
import { z } from "zod";
import type {
  ProcessingJob,
  ProcessingFilterQuery,
  ProcessingListResponse,
  ProcessingStage,
} from "./types";

export function generateStagesForJob(job: JobItem): ProcessingStage[] {
  const isSucceeded = job.status === "succeeded";
  const isFailed = job.status === "failed";
  const isRunning = job.status === "running";

  const stageDefinitions = [
    { id: "ingestion", name: "File Ingestion & Validation" },
    { id: "extraction", name: "Text Extraction & OCR" },
    { id: "chunking", name: "Chunking & Layout Analysis" },
    { id: "indexing", name: "Embedding & Vector Indexing" },
    { id: "facts", name: "Structured Fact Extraction" },
    { id: "finalizing", name: "Knowledge Synthesis" },
  ];

  return stageDefinitions.map((def, idx) => {
    if (isSucceeded) {
      return {
        id: def.id,
        name: def.name,
        status: "completed",
        durationSeconds: 1.2 + idx * 0.4,
      };
    }
    if (isFailed) {
      if (idx < 2) {
        return {
          id: def.id,
          name: def.name,
          status: "completed",
          durationSeconds: 1.1,
        };
      }
      if (idx === 2) {
        return {
          id: def.id,
          name: def.name,
          status: "failed",
          errorMessage: job.error_code || "Processing step failed due to layout parse error",
        };
      }
      return {
        id: def.id,
        name: def.name,
        status: "pending",
      };
    }
    if (isRunning) {
      if (idx < 2) {
        return {
          id: def.id,
          name: def.name,
          status: "completed",
          durationSeconds: 0.9,
        };
      }
      if (idx === 2) {
        return {
          id: def.id,
          name: def.name,
          status: "running",
        };
      }
      return {
        id: def.id,
        name: def.name,
        status: "pending",
      };
    }
    // queued / retry_wait / cancelled
    return {
      id: def.id,
      name: def.name,
      status: "pending",
    };
  });
}

export function mapBackendJobToProcessingJob(job: JobItem): ProcessingJob {
  const stages = generateStagesForJob(job);
  let progressPercent = 0;
  if (job.status === "succeeded") {
    progressPercent = 100;
  } else if (job.status === "running") {
    progressPercent = 45;
  } else if (job.status === "failed") {
    progressPercent = 35;
  } else if (job.status === "queued" || job.status === "retry_wait") {
    progressPercent = 5;
  }

  const activeStage = stages.find((s) => s.status === "running") ||
    stages.find((s) => s.status === "failed") ||
    stages[stages.length - 1];

  const payloadDocName = typeof job.payload?.filename === "string"
    ? job.payload.filename
    : typeof job.payload?.document_name === "string"
      ? job.payload.document_name
      : undefined;

  return {
    id: job.job_id,
    tenantId: job.tenant_id,
    jobType: job.job_type,
    documentId: job.resource_id,
    documentName: payloadDocName || job.resource_id,
    status: job.status,
    progressPercent,
    currentStage: activeStage?.name,
    stages,
    attempt: job.attempt,
    maxAttempts: job.max_attempts,
    errorMessage: job.error_code || undefined,
    createdAt: job.created_at,
    updatedAt: job.updated_at,
  };
}

export interface ProcessingService {
  list(query?: ProcessingFilterQuery): Promise<ProcessingListResponse>;
  getById(id: string): Promise<ProcessingJob>;
  retry(id: string): Promise<void>;
  cancel(id: string): Promise<void>;
}

export class DefaultProcessingService implements ProcessingService {
  async list(query?: ProcessingFilterQuery): Promise<ProcessingListResponse> {
    const params = new URLSearchParams();
    if (query?.status) params.set("status", query.status);
    if (query?.jobType) params.set("job_type", query.jobType);
    if (query?.limit) params.set("limit", String(query.limit));
    if (query?.cursor) params.set("cursor", query.cursor);

    const path = `/api/v1/jobs${params.toString() ? `?${params.toString()}` : ""}`;
    const response = await apiRequest(path, JobListSchema);

    let items = response.items.map(mapBackendJobToProcessingJob);

    if (query?.documentId) {
      items = items.filter((j) => j.documentId === query.documentId);
    }

    return {
      items,
      total: items.length,
      nextCursor: response.next_cursor,
    };
  }

  async getById(id: string): Promise<ProcessingJob> {
    const encodedId = encodeURIComponent(id);
    const item = await apiRequest(`/api/v1/jobs/${encodedId}`, JobSchema);
    return mapBackendJobToProcessingJob(item);
  }

  async retry(id: string): Promise<void> {
    const encodedId = encodeURIComponent(id);
    await apiRequest(`/api/v1/jobs/${encodedId}/retry`, z.unknown(), {
      method: "POST",
    });
  }

  async cancel(id: string): Promise<void> {
    const encodedId = encodeURIComponent(id);
    await apiRequest(`/api/v1/jobs/${encodedId}/cancel`, z.unknown(), {
      method: "POST",
    });
  }
}

export const defaultProcessingService = new DefaultProcessingService();
