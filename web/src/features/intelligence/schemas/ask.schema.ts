import { z } from "zod";

export const citationReferenceSchema = z.object({
  citationId: z.string().min(1),
  documentId: z.string().min(1),
  documentName: z.string(),
  pageNumber: z.number().int().positive().optional(),
  section: z.string().optional(),
  passageId: z.string().optional(),
  quote: z.string().optional(),
  sourceUrl: z.string().url().optional(),
});

export const answerClaimSchema = z.object({
  claimId: z.string().min(1),
  text: z.string(),
  citationIds: z.array(z.string()),
  supportStatus: z.enum([
    "supported",
    "partially_supported",
    "unsupported",
    "contradicted",
    "unknown",
  ]),
});

export const askResponseSchema = z.object({
  answer: z.string(),
  conversationId: z.string().optional(),
  claims: z.array(answerClaimSchema).optional(),
  citations: z.array(citationReferenceSchema),
  retrievalId: z.string().optional(),
  warnings: z.array(z.string()).optional(),
});

export type AskResponse = z.infer<typeof askResponseSchema>;
