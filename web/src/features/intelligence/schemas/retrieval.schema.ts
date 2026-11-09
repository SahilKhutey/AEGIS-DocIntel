import { z } from "zod";

export const retrievalResultSchema = z.object({
  resultId: z.string().min(1),
  documentId: z.string().min(1),
  documentName: z.string(),
  passageId: z.string().min(1),
  pageNumber: z.number().int().positive().optional(),
  section: z.string().optional(),
  text: z.string(),
  score: z.number().optional(),
  rank: z.number().int().positive().optional(),
});

export const retrievalResponseSchema = z.object({
  results: z.array(retrievalResultSchema),
  total: z.number().int().nonnegative().optional(),
  page: z.number().int().positive().optional(),
  pageSize: z.number().int().positive().optional(),
  retrievalId: z.string().optional(),
});

export type RetrievalResult = z.infer<typeof retrievalResultSchema>;
export type RetrievalResponse = z.infer<typeof retrievalResponseSchema>;
