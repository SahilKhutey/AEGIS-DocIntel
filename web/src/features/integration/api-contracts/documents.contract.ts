import { z } from "zod";

export const DocumentStatusEnum = z.enum([
  "pending",
  "indexing",
  "ready",
  "failed",
  "reindexing",
]);

export const DocumentResponseSchema = z.object({
  doc_id: z.string().min(1),
  tenant_id: z.string().min(1),
  filename: z.string().min(1),
  status: DocumentStatusEnum,
  page_count: z.number().nullable().optional(),
  chunk_count: z.number().nullable().optional(),
  is_scanned: z.boolean().default(false),
  language: z.string().default("en"),
  created_at: z.string(),
  indexed_at: z.string().nullable().optional(),
});

export const DocumentListResponseSchema = z.object({
  items: z.array(DocumentResponseSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive().default(1),
  page_size: z.number().int().positive().default(20),
});

export type DocumentResponse = z.infer<typeof DocumentResponseSchema>;
export type DocumentListResponse = z.infer<typeof DocumentListResponseSchema>;
