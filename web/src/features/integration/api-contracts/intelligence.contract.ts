import { z } from "zod";

export const CitationSchema = z.object({
  citation_id: z.string().optional(),
  chunk_id: z.string().min(1),
  doc_id: z.string().min(1),
  page: z.number().int().optional(),
  text: z.string().optional(),
  relevance_score: z.number().optional(),
});

export const QueryResponseSchema = z.object({
  answer: z.string(),
  citations: z.array(CitationSchema).default([]),
  confidence: z.unknown(),
  confidence_score: z.number().nullable().optional(),
  session_id: z.string().nullable().optional(),
  tokens_used: z.union([
    z.number().int(),
    z.object({
      input: z.number().int().optional(),
      output: z.number().int().optional(),
      total: z.number().int().optional(),
    }),
  ]),
  retrieval_latency_ms: z.number().nullable().optional(),
  total_latency_ms: z.number().nullable().optional(),
  cached: z.boolean().default(false),
  model: z.string(),
  grounded: z.boolean().nullable().optional(),
});

export const StreamChunkSchema = z.object({
  type: z.enum(["token", "citation", "done", "error"]),
  content: z.string().nullable().optional(),
  citations: z.array(CitationSchema).nullable().optional(),
  error: z.string().nullable().optional(),
});

export type Citation = z.infer<typeof CitationSchema>;
export type QueryResponse = z.infer<typeof QueryResponseSchema>;
export type StreamChunk = z.infer<typeof StreamChunkSchema>;
