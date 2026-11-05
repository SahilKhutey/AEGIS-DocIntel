import { z } from "zod";

// ── Document Schemas ──────────────────────────────────────────────
export const DocumentStatusSchema = z.enum([
  "pending",
  "indexing",
  "ready",
  "failed",
  "reindexing",
]);

export const DocumentSchema = z.object({
  doc_id: z.string().min(1),
  tenant_id: z.string().optional(),
  filename: z.string().min(1),
  status: DocumentStatusSchema,
  page_count: z.number().int().nonnegative().nullable().optional(),
  chunk_count: z.number().int().nonnegative().nullable().optional(),
  is_scanned: z.boolean().optional().default(false),
  language: z.string().optional().default("en"),
  created_at: z.string(),
  indexed_at: z.string().nullable().optional(),
});

export const DocumentListSchema = z.object({
  items: z.array(DocumentSchema),
  total: z.number(),
  page: z.number(),
  page_size: z.number(),
});

export const DocumentChunkSchema = z.object({
  chunk_id: z.string(),
  doc_id: z.string(),
  text: z.string(),
  page_number: z.number().nullable().optional(),
  section_title: z.string().nullable().optional(),
});

export const DocumentChunkListSchema = z.object({
  items: z.array(DocumentChunkSchema).optional().default([]),
  total: z.number().optional().default(0),
});

// ── Evidence & Question-Answering Schemas ──────────────────────────
export const EvidenceSchema = z.object({
  evidence_id: z.string().optional(),
  document_id: z.string().min(1),
  chunk_id: z.string().default(""),
  quote: z.string().default(""),
  page_number: z.number().int().positive().nullable().optional(),
  section_path: z.array(z.string()).optional().default([]),
});

export const AnswerCitationSchema = z.object({
  evidence_id: z.string(),
  document_id: z.string(),
  page_number: z.number().nullable().optional(),
  section_path: z.array(z.string()).optional().default([]),
});

export const AnswerSchema = z.object({
  status: z.string().optional().default("grounded"),
  answer: z.string(),
  citations: z.array(AnswerCitationSchema).optional().default([]),
  evidence: z.array(EvidenceSchema).optional().default([]),
  warnings: z.array(z.string()).optional().default([]),
  insufficient_evidence: z.boolean().optional().default(false),
  request_id: z.string().optional(),
});

// ── Review & Governance Schemas ───────────────────────────────────
export const ReviewStatusSchema = z.enum([
  "pending",
  "in_review",
  "approved",
  "corrected",
  "rejected",
  "needs_evidence",
]);

export const ReviewActionSchema = z.enum([
  "create",
  "claim",
  "approve",
  "correct",
  "reject",
  "request_evidence",
  "reopen",
]);

export const ReviewRevisionSchema = z.object({
  revision_id: z.string(),
  review_id: z.string(),
  tenant_id: z.string(),
  actor_id: z.string(),
  version: z.number(),
  corrected_value: z.unknown(),
  corrected_type: z.string(),
  unit: z.string().nullable().optional(),
  evidence_quote: z.string().nullable().optional(),
  rationale: z.string(),
  created_at: z.string(),
});

export const ReviewItemSchema = z.object({
  review_id: z.string().min(1),
  tenant_id: z.string(),
  candidate_id: z.string().min(1),
  candidate_type: z.enum(["fact", "conflict"]),
  document_id: z.string(),
  status: ReviewStatusSchema,
  version: z.number().int().positive(),
  assigned_to: z.string().nullable().optional(),
  candidate_data: z.record(z.string(), z.unknown()),
  current_revision_id: z.string().nullable().optional(),
  current_revision: ReviewRevisionSchema.nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const ReviewListSchema = z.object({
  items: z.array(ReviewItemSchema),
  next_cursor: z.string().nullable().optional(),
});

export const AuditEventSchema = z.object({
  event_id: z.string(),
  review_id: z.string(),
  sequence: z.number(),
  tenant_id: z.string(),
  actor_id: z.string(),
  action: z.string(),
  previous_status: z.string(),
  new_status: z.string(),
  previous_version: z.number(),
  new_version: z.number(),
  rationale: z.string(),
  revision_id: z.string().nullable().optional(),
  request_id: z.string().nullable().optional(),
  timestamp: z.string(),
});

export const DecisionResponseSchema = z.object({
  item: ReviewItemSchema,
  decision: z.record(z.string(), z.unknown()),
  audit_event: AuditEventSchema,
});

export const GovernanceMetricsSchema = z.object({
  total_items: z.number(),
  decided_count: z.number(),
  approval_rate: z.number(),
  correction_rate: z.number(),
  rejection_rate: z.number(),
  evidence_failure_rate: z.number(),
  feedback_categories: z.record(z.string(), z.number()).optional().default({}),
});

// ── Intelligence & Comparison Schemas ─────────────────────────────
export const ExtractedFactSchema = z.object({
  fact_id: z.string(),
  tenant_id: z.string(),
  document_id: z.string(),
  subject: z.string(),
  attribute: z.string(),
  value: z.unknown(),
  raw_value: z.string(),
  value_type: z.string(),
  unit: z.string().nullable().optional(),
  confidence: z.number().optional().default(1.0),
  evidence: z.array(z.record(z.string(), z.unknown())).optional().default([]),
});

export const DocumentComparisonSchema = z.object({
  document_ids: z.array(z.string()),
  compared_at: z.string(),
  total_pairs: z.number(),
  matching_pairs: z.number(),
  conflicting_pairs: z.number(),
  comparisons: z.array(z.record(z.string(), z.unknown())).optional().default([]),
  conflicts: z.array(z.record(z.string(), z.unknown())).optional().default([]),
});

// ── Inferred Types ────────────────────────────────────────────────
export type DocumentItem = z.infer<typeof DocumentSchema>;
export type DocumentList = z.infer<typeof DocumentListSchema>;
export type DocumentChunk = z.infer<typeof DocumentChunkSchema>;
export type Evidence = z.infer<typeof EvidenceSchema>;
export type AnswerCitation = z.infer<typeof AnswerCitationSchema>;
export type AnswerResult = z.infer<typeof AnswerSchema>;
export type ReviewItem = z.infer<typeof ReviewItemSchema>;
export type ReviewList = z.infer<typeof ReviewListSchema>;
export type ReviewRevision = z.infer<typeof ReviewRevisionSchema>;
export type AuditEvent = z.infer<typeof AuditEventSchema>;
export type DecisionResponse = z.infer<typeof DecisionResponseSchema>;
export type GovernanceMetrics = z.infer<typeof GovernanceMetricsSchema>;
export type ExtractedFact = z.infer<typeof ExtractedFactSchema>;
export type DocumentComparison = z.infer<typeof DocumentComparisonSchema>;

// ── Operational Job Schemas ───────────────────────────────────────
export const JobStatusSchema = z.enum([
  "queued",
  "running",
  "retry_wait",
  "succeeded",
  "failed",
  "cancelled",
]);

export const JobTypeSchema = z.enum([
  "ingest_document",
  "index_document",
  "extract_facts",
  "compare_documents",
  "generate_report",
]);

export const JobSchema = z.object({
  job_id: z.string(),
  tenant_id: z.string(),
  job_type: z.string(),
  resource_id: z.string(),
  status: JobStatusSchema,
  attempt: z.number().int().nonnegative(),
  max_attempts: z.number().int().positive(),
  version: z.number().int().positive(),
  idempotency_key: z.string(),
  input_fingerprint: z.string(),
  requested_by: z.string(),
  lease_owner: z.string().nullable().optional(),
  lease_expires_at: z.string().nullable().optional(),
  next_attempt_at: z.string().nullable().optional(),
  result_reference: z.string().nullable().optional(),
  error_code: z.string().nullable().optional(),
  payload: z.record(z.string(), z.unknown()).optional().default({}),
  created_at: z.string(),
  updated_at: z.string(),
  status_url: z.string().optional(),
});

export const JobListSchema = z.object({
  items: z.array(JobSchema),
  next_cursor: z.string().nullable().optional(),
});

export const JobEventItemSchema = z.object({
  event_id: z.string(),
  job_id: z.string(),
  sequence: z.number(),
  tenant_id: z.string(),
  from_status: z.string(),
  to_status: z.string(),
  attempt: z.number(),
  worker_id: z.string().nullable().optional(),
  error_code: z.string().nullable().optional(),
  message: z.string().nullable().optional(),
  timestamp: z.string(),
});

export type JobItem = z.infer<typeof JobSchema>;
export type JobList = z.infer<typeof JobListSchema>;
export type JobEventItem = z.infer<typeof JobEventItemSchema>;
