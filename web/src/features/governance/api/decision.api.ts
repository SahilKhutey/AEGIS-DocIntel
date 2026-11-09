import { apiRequest } from "@/lib/api-client";
import {
  DecisionInputSchema,
  DecisionResponseSchema,
  FeedbackInputSchema,
  type DecisionInput,
  type DecisionResponse,
  type FeedbackInput,
} from "../schemas/decision.schema";
import { z } from "zod";

export async function submitReviewDecision(
  reviewId: string,
  input: DecisionInput,
  idempotencyKey?: string,
): Promise<DecisionResponse> {
  const validated = DecisionInputSchema.parse(input);
  const encodedId = encodeURIComponent(reviewId);

  const headers: Record<string, string> = {};
  if (idempotencyKey) {
    headers["Idempotency-Key"] = idempotencyKey;
  }

  const response = await apiRequest(
    `/api/v1/reviews/${encodedId}/decisions`,
    DecisionResponseSchema,
    {
      method: "POST",
      headers,
      body: JSON.stringify(validated),
    },
  );

  return response as DecisionResponse;
}

export async function submitReviewFeedback(
  reviewId: string,
  feedback: FeedbackInput,
): Promise<{ status: string }> {
  const validated = FeedbackInputSchema.parse(feedback);
  const encodedId = encodeURIComponent(reviewId);

  return apiRequest(
    `/api/v1/reviews/${encodedId}/feedback`,
    z.object({ status: z.string() }),
    {
      method: "POST",
      body: JSON.stringify(validated),
    },
  );
}
