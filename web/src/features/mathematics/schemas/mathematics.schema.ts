import { z } from "zod";

export const ProvenanceSchema = z.object({
  sourceDocumentId: z.string(),
  sourceDocumentTitle: z.string(),
  model: z.string(),
  poolingMethod: z.string(),
  checksum: z.string(),
  generatedAt: z.string(),
});

export const VectorRepresentationSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.literal("vector"),
  dimensions: z.number().int().positive(),
  precision: z.enum(["float32", "float64"]),
  l2Norm: z.number(),
  min: z.number(),
  max: z.number(),
  sparsity: z.number().min(0).max(100),
  values: z.array(z.number()),
  provenance: ProvenanceSchema,
});

export const MatrixRepresentationSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.literal("matrix"),
  rows: z.number().int().positive(),
  cols: z.number().int().positive(),
  sparsity: z.number().min(0).max(100),
  conditionNumber: z.number().optional(),
  matrix: z.array(z.array(z.number())),
  rowLabels: z.array(z.string()).optional(),
  colLabels: z.array(z.string()).optional(),
  provenance: ProvenanceSchema,
});
