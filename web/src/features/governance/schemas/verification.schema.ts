import { z } from "zod";

export const FactVerificationStatusSchema = z.enum([
  "verified",
  "partially_verified",
  "not_verified",
  "contradicted",
  "insufficient_evidence",
]);

export const EvidenceReferenceSchema = z.object({
  evidence_id: z.string().optional(),
  document_id: z.string().min(1),
  chunk_id: z.string().optional(),
  page_number: z.number().int().optional(),
  quote: z.string().min(1),
  confidence: z.number().min(0).max(1).optional(),
  section_path: z.array(z.string()).optional(),
});

export const FactVerificationInputSchema = z.object({
  verification_status: FactVerificationStatusSchema,
  rationale: z.string().trim().min(3, "Rationale must be at least 3 characters").max(2000),
  selected_evidence_id: z.string().optional(),
  verified_quote: z.string().optional(),
});

export type FactVerificationInput = z.infer<typeof FactVerificationInputSchema>;
