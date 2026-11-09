import { z } from "zod";

export const ConflictResolutionOutcomeSchema = z.enum([
  "accepted_first_fact",
  "accepted_second_fact",
  "both_valid",
  "insufficient_evidence",
  "escalated",
]);

export const ConflictingClaimSchema = z.object({
  fact_id: z.string().optional(),
  document_id: z.string(),
  value: z.unknown(),
  raw_value: z.string().optional(),
  confidence: z.number().optional(),
  evidence_quote: z.string().optional(),
  page_number: z.number().optional(),
  published_date: z.string().optional(),
});

export const ConflictReportSchema = z.object({
  conflict_id: z.string().optional(),
  subject: z.string(),
  attribute: z.string(),
  fact_1: ConflictingClaimSchema,
  fact_2: ConflictingClaimSchema,
  contradiction_type: z.string().optional(),
  conflicting_document_ids: z.array(z.string()).optional(),
  severity: z.enum(["critical", "high", "medium", "low"]).optional(),
});

export const ConflictResolutionInputSchema = z.object({
  outcome: ConflictResolutionOutcomeSchema,
  rationale: z.string().trim().min(5, "Resolution rationale must be at least 5 characters").max(2000),
  reconciled_value: z.union([z.string(), z.number(), z.boolean()]).optional(),
  reconciled_evidence_quote: z.string().optional(),
});

export type ConflictResolutionInput = z.infer<typeof ConflictResolutionInputSchema>;
