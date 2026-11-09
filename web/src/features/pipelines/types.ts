export type PipelineJobStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type PipelineStageStatus =
  | "idle"
  | "running"
  | "succeeded"
  | "failed"
  | "skipped";

export interface PipelineStage {
  id: string;
  name: string;
  status: PipelineStageStatus;
  dependsOn: string[]; // Node IDs that this stage depends on
  durationMs?: number;
  workerId?: string;
  error?: {
    code: string;
    message: string;
    details?: string;
  };
  metrics?: Record<string, string | number>;
}

export interface PipelineRun {
  id: string;
  jobType: string;
  resourceId: string;
  resourceTitle: string;
  status: PipelineJobStatus;
  attempt: number;
  maxAttempts: number;
  errorCode?: string | null;
  stages: PipelineStage[];
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

export interface PipelineEvent {
  sequence: number;
  fromStatus: string;
  toStatus: string;
  workerId: string;
  errorCode: string | null;
  message: string;
  timestamp: string;
}

export interface GraphNode {
  id: string;
  label: string;
  status: PipelineStageStatus;
  durationMs?: number;
}

export interface GraphEdge {
  from: string;
  to: string;
}
