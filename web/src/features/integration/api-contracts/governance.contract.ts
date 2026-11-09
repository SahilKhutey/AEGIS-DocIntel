import { z } from "zod";

export const ReviewStatusEnum = z.enum([
  "PENDING",
  "IN_PROGRESS",
  "APPROVED",
  "CORRECTED",
  "REJECTED",
  "ESCALATED",
]);

export const ReviewItemResponseSchema = z.object({
  id: z.string().min(1),
  tenant_id: z.string().min(1),
  document_id: z.string().min(1),
  document_title: z.string(),
  status: ReviewStatusEnum,
  priority: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]).default("MEDIUM"),
  assigned_to: z.string().nullable().optional(),
  fact_count: z.number().int().default(0),
  conflict_count: z.number().int().default(0),
  created_at: z.string(),
  updated_at: z.string(),
});

export const ReviewQueueResponseSchema = z.object({
  items: z.array(ReviewItemResponseSchema),
  total: z.number().int().nonnegative(),
});

export const ReviewDecisionRequestSchema = z.object({
  review_id: z.string().min(1),
  decision: z.enum(["APPROVE", "CORRECT", "REJECT", "ESCALATE"]),
  rationale: z.string().min(1),
  confirmed: z.literal(true),
});

export type ReviewItemResponse = z.infer<typeof ReviewItemResponseSchema>;
export type ReviewQueueResponse = z.infer<typeof ReviewQueueResponseSchema>;
export type ReviewDecisionRequest = z.infer<typeof ReviewDecisionRequestSchema>;
