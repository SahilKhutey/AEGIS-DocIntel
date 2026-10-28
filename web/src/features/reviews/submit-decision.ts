import { z } from "zod";
import { apiRequest } from "@/lib/api-client";
import { ReviewItemSchema, type ReviewItem, DecisionResponseSchema } from "@/lib/schemas";

export type ReviewAction =
  | "approve"
  | "correct"
  | "reject"
  | "request_evidence";

export const DecisionInputSchema = z.object({
  action: z.enum([
    "approve",
    "correct",
    "reject",
    "request_evidence",
  ]),
  expected_version: z.number().int().positive(),
  rationale: z.string().trim().min(3, "Rationale must be at least 3 characters").max(2000),
  corrected_value: z.union([
    z.string(),
    z.number(),
    z.boolean(),
  ]).optional(),
  corrected_type: z.string().optional(),
  unit: z.string().optional(),
  evidence_quote: z.string().max(5000).optional(),
});

export type DecisionInput = z.infer<typeof DecisionInputSchema>;

export async function submitReviewDecision(
  reviewId: string,
  input: DecisionInput,
  idempotencyKey?: string,
): Promise<{ item: ReviewItem; decision: Record<string, unknown>; audit_event: Record<string, unknown> }> {
  // Client-side schema validation
  const validated = DecisionInputSchema.parse(input);
  const id = encodeURIComponent(reviewId);

  const headers: Record<string, string> = {};
  if (idempotencyKey) {
    headers["Idempotency-Key"] = idempotencyKey;
  }

  const response = await apiRequest(
    `/api/v1/reviews/${id}/decisions`,
    DecisionResponseSchema,
    {
      method: "POST",
      headers,
      body: JSON.stringify(validated),
    },
  );

  return response as { item: ReviewItem; decision: Record<string, unknown>; audit_event: Record<string, unknown> };
}

export async function claimReviewItem(
  reviewId: string,
  expectedVersion: number,
): Promise<ReviewItem> {
  const id = encodeURIComponent(reviewId);
  return apiRequest(
    `/api/v1/reviews/${id}/claim`,
    ReviewItemSchema,
    {
      method: "POST",
      body: JSON.stringify({ expected_version: expectedVersion }),
    },
  );
}

export async function reopenReviewItem(
  reviewId: string,
  expectedVersion: number,
  rationale: string,
): Promise<{ item: ReviewItem }> {
  const id = encodeURIComponent(reviewId);
  return apiRequest(
    `/api/v1/reviews/${id}/reopen`,
    z.object({ item: ReviewItemSchema }),
    {
      method: "POST",
      body: JSON.stringify({
        expected_version: expectedVersion,
        rationale,
      }),
    },
  );
}
