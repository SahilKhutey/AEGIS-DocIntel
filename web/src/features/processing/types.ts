export type ProcessingStageStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "skipped";

export type ProcessingJobStatus =
  | "queued"
  | "running"
  | "retry_wait"
  | "succeeded"
  | "failed"
  | "cancelled";

export type ProcessingStage = {
  id: string;
  name: string;
  status: ProcessingStageStatus;
  startedAt?: string;
  completedAt?: string;
  durationSeconds?: number;
  errorMessage?: string;
};

export type ProcessingJob = {
  id: string;
  tenantId: string;
  jobType: string;
  documentId: string;
  documentName?: string;
  status: ProcessingJobStatus;
  progressPercent: number;
  currentStage?: string;
  stages?: ProcessingStage[];
  attempt: number;
  maxAttempts: number;
  errorMessage?: string;
  createdAt: string;
  updatedAt: string;
};

export type ProcessingListResponse = {
  items: ProcessingJob[];
  total: number;
  nextCursor?: string | null;
};

export type ProcessingFilterQuery = {
  status?: ProcessingJobStatus;
  jobType?: string;
  documentId?: string;
  limit?: number;
  cursor?: string;
};
