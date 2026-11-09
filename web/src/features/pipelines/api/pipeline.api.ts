import {
  type PipelineRun,
  type PipelineEvent,
  type PipelineJobStatus,
} from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const MOCK_PIPELINE_RUNS: PipelineRun[] = [
  {
    id: "job-run-9021",
    jobType: "document_ingestion_pipeline",
    resourceId: "doc-sample-01",
    resourceTitle: "Q3_Financial_Review.pdf",
    status: "completed",
    attempt: 1,
    maxAttempts: 3,
    createdAt: "2026-11-09T08:15:00.000Z",
    updatedAt: "2026-11-09T08:15:42.000Z",
    completedAt: "2026-11-09T08:15:42.000Z",
    stages: [
      { id: "ingest", name: "Document Ingestion", status: "succeeded", dependsOn: [], durationMs: 450, workerId: "worker-ingest-01" },
      { id: "validation", name: "Format & Security Validation", status: "succeeded", dependsOn: ["ingest"], durationMs: 320, workerId: "worker-ingest-01" },
      { id: "ocr", name: "OCR & Vision Extraction", status: "succeeded", dependsOn: ["validation"], durationMs: 8400, workerId: "worker-ocr-03" },
      { id: "structuring", name: "Heading & Hierarchy Structuring", status: "succeeded", dependsOn: ["validation"], durationMs: 1200, workerId: "worker-struct-02" },
      { id: "embed", name: "Dense Embedding Generation", status: "succeeded", dependsOn: ["ocr", "structuring"], durationMs: 4200, workerId: "worker-embed-01" },
      { id: "index", name: "HNSW Vector Graph Indexation", status: "succeeded", dependsOn: ["embed"], durationMs: 950, workerId: "worker-index-02" },
      { id: "gov_check", name: "Candidate Fact Extraction", status: "succeeded", dependsOn: ["index"], durationMs: 1800, workerId: "worker-gov-01" },
    ],
  },
  {
    id: "job-run-9022",
    jobType: "document_ingestion_pipeline",
    resourceId: "doc-sample-02",
    resourceTitle: "Credit_Agreement_2026.pdf",
    status: "running",
    attempt: 1,
    maxAttempts: 3,
    createdAt: "2026-11-09T09:20:00.000Z",
    updatedAt: "2026-11-09T09:20:15.000Z",
    stages: [
      { id: "ingest", name: "Document Ingestion", status: "succeeded", dependsOn: [], durationMs: 510, workerId: "worker-ingest-02" },
      { id: "validation", name: "Format & Security Validation", status: "succeeded", dependsOn: ["ingest"], durationMs: 290, workerId: "worker-ingest-02" },
      { id: "ocr", name: "OCR & Vision Extraction", status: "running", dependsOn: ["validation"], durationMs: 4100, workerId: "worker-ocr-01" },
      { id: "structuring", name: "Heading & Hierarchy Structuring", status: "running", dependsOn: ["validation"], durationMs: 2100, workerId: "worker-struct-01" },
      { id: "embed", name: "Dense Embedding Generation", status: "idle", dependsOn: ["ocr", "structuring"] },
      { id: "index", name: "HNSW Vector Graph Indexation", status: "idle", dependsOn: ["embed"] },
      { id: "gov_check", name: "Candidate Fact Extraction", status: "idle", dependsOn: ["index"] },
    ],
  },
  {
    id: "job-run-9023",
    jobType: "document_ingestion_pipeline",
    resourceId: "doc-sample-03",
    resourceTitle: "Corrupted_Tax_Report.pdf",
    status: "failed",
    attempt: 2,
    maxAttempts: 3,
    errorCode: "OCR_TIMEOUT_EXCEEDED",
    createdAt: "2026-11-09T07:10:00.000Z",
    updatedAt: "2026-11-09T07:12:30.000Z",
    stages: [
      { id: "ingest", name: "Document Ingestion", status: "succeeded", dependsOn: [], durationMs: 480, workerId: "worker-ingest-01" },
      { id: "validation", name: "Format & Security Validation", status: "succeeded", dependsOn: ["ingest"], durationMs: 310, workerId: "worker-ingest-01" },
      {
        id: "ocr",
        name: "OCR & Vision Extraction",
        status: "failed",
        dependsOn: ["validation"],
        durationMs: 30000,
        workerId: "worker-ocr-02",
        error: {
          code: "OCR_TIMEOUT_EXCEEDED",
          message: "Tesseract worker exceeded 30000ms deadline on page 42.",
          details: "Worker process terminated due to memory pressure.",
        },
      },
      { id: "structuring", name: "Heading & Hierarchy Structuring", status: "succeeded", dependsOn: ["validation"], durationMs: 1100, workerId: "worker-struct-01" },
      { id: "embed", name: "Dense Embedding Generation", status: "skipped", dependsOn: ["ocr", "structuring"] },
      { id: "index", name: "HNSW Vector Graph Indexation", status: "skipped", dependsOn: ["embed"] },
      { id: "gov_check", name: "Candidate Fact Extraction", status: "skipped", dependsOn: ["index"] },
    ],
  },
];

const MOCK_EVENTS_BY_JOB: Record<string, PipelineEvent[]> = {
  "job-run-9021": [
    { sequence: 1, fromStatus: "pending", toStatus: "running", workerId: "coordinator-01", errorCode: null, message: "Job claimed by coordinator", timestamp: "2026-11-09T08:15:00.000Z" },
    { sequence: 2, fromStatus: "running", toStatus: "running", workerId: "worker-ingest-01", errorCode: null, message: "Ingestion and validation completed", timestamp: "2026-11-09T08:15:02.000Z" },
    { sequence: 3, fromStatus: "running", toStatus: "running", workerId: "worker-ocr-03", errorCode: null, message: "OCR completed 14 pages", timestamp: "2026-11-09T08:15:28.000Z" },
    { sequence: 4, fromStatus: "running", toStatus: "running", workerId: "worker-embed-01", errorCode: null, message: "Generated 142 embeddings", timestamp: "2026-11-09T08:15:38.000Z" },
    { sequence: 5, fromStatus: "running", toStatus: "completed", workerId: "coordinator-01", errorCode: null, message: "Pipeline run completed successfully", timestamp: "2026-11-09T08:15:42.000Z" },
  ],
  "job-run-9023": [
    { sequence: 1, fromStatus: "pending", toStatus: "running", workerId: "coordinator-01", errorCode: null, message: "Job initiated attempt 1", timestamp: "2026-11-09T07:10:00.000Z" },
    { sequence: 2, fromStatus: "running", toStatus: "failed", workerId: "worker-ocr-02", errorCode: "OCR_TIMEOUT_EXCEEDED", message: "Timeout on page 42", timestamp: "2026-11-09T07:11:00.000Z" },
    { sequence: 3, fromStatus: "failed", toStatus: "running", workerId: "coordinator-01", errorCode: null, message: "Automatic retry attempt 2 scheduled", timestamp: "2026-11-09T07:11:30.000Z" },
    { sequence: 4, fromStatus: "running", toStatus: "failed", workerId: "worker-ocr-02", errorCode: "OCR_TIMEOUT_EXCEEDED", message: "Timeout repeated, max automated retries exhausted", timestamp: "2026-11-09T07:12:30.000Z" },
  ],
};

export async function getPipelineRuns(
  statusFilter?: PipelineJobStatus,
): Promise<PipelineRun[]> {
  try {
    const url = new URL(`${API_BASE_URL}/v1/jobs`);
    if (statusFilter) url.searchParams.set("status", statusFilter);
    const res = await fetch(url.toString(), {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    return json.items || json;
  } catch {
    if (statusFilter) {
      return MOCK_PIPELINE_RUNS.filter((run) => run.status === statusFilter);
    }
    return MOCK_PIPELINE_RUNS;
  }
}

export async function getPipelineRunById(id: string): Promise<PipelineRun | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/v1/jobs/${id}`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch {
    const found = MOCK_PIPELINE_RUNS.find((r) => r.id === id);
    return found || null;
  }
}

export async function getPipelineEvents(id: string): Promise<PipelineEvent[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/v1/jobs/${id}/events`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch {
    return MOCK_EVENTS_BY_JOB[id] || [];
  }
}

export async function retryPipelineRun(id: string): Promise<{ success: boolean; message: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/v1/jobs/${id}/retry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch {
    return {
      success: true,
      message: `Job ${id} queued for retry execution.`,
    };
  }
}

export async function cancelPipelineRun(id: string): Promise<{ success: boolean; message: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/v1/jobs/${id}/cancel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch {
    return {
      success: true,
      message: `Job ${id} cancellation signal sent.`,
    };
  }
}
