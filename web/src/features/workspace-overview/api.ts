import { defaultDocumentService, type DocumentService } from "../documents/api";
import { defaultProcessingService, type ProcessingService } from "../processing/api";
import type { WorkspaceOverviewData, AttentionItem, WorkspaceMetrics } from "./types";

export async function fetchWorkspaceOverview(
  docService: DocumentService = defaultDocumentService,
  procService: ProcessingService = defaultProcessingService
): Promise<WorkspaceOverviewData> {
  const [docList, jobList] = await Promise.allSettled([
    docService.list({ limit: 100 }),
    procService.list({ limit: 50 }),
  ]);

  const docs = docList.status === "fulfilled" ? docList.value.items : [];
  const totalDocs = docList.status === "fulfilled" ? docList.value.total : 0;
  const jobs = jobList.status === "fulfilled" ? jobList.value.items : [];

  let processingCount = 0;
  let completedCount = 0;
  let failedCount = 0;
  let queuedCount = 0;

  for (const doc of docs) {
    if (doc.status === "processing") processingCount++;
    else if (doc.status === "completed") completedCount++;
    else if (doc.status === "failed") failedCount++;
    else if (doc.status === "queued" || doc.status === "uploaded") queuedCount++;
  }

  const activeJobs = jobs.filter(
    (j) => j.status === "running" || j.status === "queued" || j.status === "retry_wait"
  ).length;

  const attentionItems: AttentionItem[] = [];

  // Attention: failed documents
  for (const doc of docs.filter((d) => d.status === "failed")) {
    attentionItems.push({
      id: `doc-${doc.id}`,
      title: doc.name,
      description: "Document ingestion/indexing failed. Requires reindexing or file verification.",
      type: "failed_document",
      link: `/documents/${encodeURIComponent(doc.id)}`,
      timestamp: doc.updatedAt,
    });
  }

  // Attention: failed jobs
  for (const job of jobs.filter((j) => j.status === "failed")) {
    attentionItems.push({
      id: `job-${job.id}`,
      title: `Job: ${job.documentName || job.documentId}`,
      description: job.errorMessage || "Processing job failed. Retry available.",
      type: "failed_job",
      link: "/processing",
      timestamp: job.updatedAt,
    });
  }

  const metrics: WorkspaceMetrics = {
    totalDocuments: totalDocs || docs.length,
    processingDocuments: processingCount,
    completedDocuments: completedCount,
    failedDocuments: failedCount,
    queuedDocuments: queuedCount,
    activeJobs,
    attentionCount: attentionItems.length,
  };

  return {
    metrics,
    recentDocuments: docs.slice(0, 5),
    recentJobs: jobs.slice(0, 5),
    attentionItems: attentionItems.slice(0, 5),
  };
}
