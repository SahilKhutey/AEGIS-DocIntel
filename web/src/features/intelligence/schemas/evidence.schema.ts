import { z } from "zod";

export const evidenceRecordSchema = z.object({
  evidenceId: z.string().min(1),
  documentId: z.string().min(1),
  documentName: z.string(),
  passageId: z.string().optional(),
  pageNumber: z.number().int().positive().optional(),
  section: z.string().optional(),
  content: z.string(),
  evidenceType: z.string().optional(),
  relatedCitationIds: z.array(z.string()).optional(),
});

export const evidenceListResponseSchema = z.object({
  items: z.array(evidenceRecordSchema),
  total: z.number().int().nonnegative().optional(),
});

export type EvidenceRecord = z.infer<typeof evidenceRecordSchema>;
export type EvidenceListResponse = z.infer<typeof evidenceListResponseSchema>;
