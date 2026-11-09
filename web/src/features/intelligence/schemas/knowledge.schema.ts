import { z } from "zod";

export const knowledgeNodeSchema = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
  type: z.string().min(1),
  documentIds: z.array(z.string()).optional(),
});

export const knowledgeEdgeSchema = z.object({
  id: z.string().min(1),
  source: z.string().min(1),
  target: z.string().min(1),
  relationship: z.string().min(1),
});

export const knowledgeGraphResponseSchema = z.object({
  nodes: z.array(knowledgeNodeSchema),
  edges: z.array(knowledgeEdgeSchema),
});

export type KnowledgeNode = z.infer<typeof knowledgeNodeSchema>;
export type KnowledgeEdge = z.infer<typeof knowledgeEdgeSchema>;
export type KnowledgeGraphResponse = z.infer<typeof knowledgeGraphResponseSchema>;
