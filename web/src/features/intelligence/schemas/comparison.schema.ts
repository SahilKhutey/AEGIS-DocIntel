import { z } from "zod";
import { citationReferenceSchema } from "./ask.schema";

export const comparisonDifferenceSchema = z.object({
  differenceId: z.string().min(1),
  category: z.string().min(1),
  description: z.string(),
  leftEvidence: citationReferenceSchema.optional(),
  rightEvidence: citationReferenceSchema.optional(),
  significance: z
    .enum(["low", "medium", "high", "unknown"])
    .optional()
    .default("unknown"),
});

export const comparisonResponseSchema = z.object({
  comparisonId: z.string().min(1),
  documentIds: z.array(z.string()),
  differences: z.array(comparisonDifferenceSchema),
  summary: z.string().optional(),
});

export type ComparisonDifference = z.infer<typeof comparisonDifferenceSchema>;
export type ComparisonResponse = z.infer<typeof comparisonResponseSchema>;
