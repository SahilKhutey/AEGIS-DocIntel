import type { DocumentRecord } from "../documents/types";
import type { ProcessingJob } from "../processing/types";

export type WorkspaceMetrics = {
  totalDocuments: number;
  processingDocuments: number;
  completedDocuments: number;
  failedDocuments: number;
  queuedDocuments: number;
  activeJobs: number;
  attentionCount: number;
};

export type AttentionItem = {
  id: string;
  title: string;
  description: string;
  type: "failed_document" | "failed_job" | "review_pending";
  link: string;
  timestamp: string;
};

export type WorkspaceOverviewData = {
  metrics: WorkspaceMetrics;
  recentDocuments: DocumentRecord[];
  recentJobs: ProcessingJob[];
  attentionItems: AttentionItem[];
};
