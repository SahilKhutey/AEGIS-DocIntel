import { z } from "zod";

export const ReviewStatusSchema = z.enum([
  "pending",
  "in_review",
  "approved",
  "corrected",
  "rejected",
  "needs_evidence",
]);

export const CandidateTypeSchema = z.enum(["fact", "conflict"]);

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
  candidate_type: CandidateTypeSchema,
  document_id: z.string(),
  status: ReviewStatusSchema,
  version: z.number().int().positive(),
  assigned_to: z.string().nullable().optional(),
  candidate_data: z.record(z.string(), z.unknown()),
  current_revision_id: z.string().nullable().optional(),
  current_revision: ReviewRevisionSchema.nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
  field_name: z.string().optional(),
  extracted_value: z.string().optional(),
  page_number: z.number().optional(),
  confidence: z.number().optional(),
});

export const ReviewListSchema = z.object({
  items: z.array(ReviewItemSchema),
  next_cursor: z.string().nullable().optional(),
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
