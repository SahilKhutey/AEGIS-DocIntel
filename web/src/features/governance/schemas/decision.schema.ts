import { z } from "zod";
import { ReviewItemSchema } from "./review.schema";

export const DecisionTypeSchema = z.enum([
  "approve",
  "correct",
  "reject",
  "request_evidence",
]);

export const DecisionInputSchema = z.object({
  action: DecisionTypeSchema,
  expected_version: z.number().int().positive(),
  rationale: z.string().trim().min(3, "Rationale must be at least 3 characters").max(2000),
  corrected_value: z.union([z.string(), z.number(), z.boolean()]).optional(),
  corrected_type: z.string().optional(),
  unit: z.string().optional(),
  evidence_quote: z.string().max(5000).optional(),
});

export const DecisionResponseSchema = z.object({
  item: ReviewItemSchema,
  decision: z.record(z.string(), z.unknown()),
  audit_event: z.record(z.string(), z.unknown()),
});

export const FeedbackInputSchema = z.object({
  category: z.enum([
    "wrong_value",
    "wrong_attribute",
    "bad_evidence",
    "hallucination",
    "missing_context",
    "other",
  ]),
  notes: z.string().max(2000).optional().default(""),
});

export type DecisionInput = z.infer<typeof DecisionInputSchema>;
export type DecisionResponse = z.infer<typeof DecisionResponseSchema>;
export type FeedbackInput = z.infer<typeof FeedbackInputSchema>;
