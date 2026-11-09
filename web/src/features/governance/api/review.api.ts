import { apiRequest } from "@/lib/api-client";
import {
  ReviewListSchema,
  ReviewItemSchema,
  GovernanceMetricsSchema,
} from "../schemas/review.schema";
import type { ReviewItem, GovernanceMetrics } from "../types";
import { z } from "zod";

export interface ReviewQueueParams {
  status?: string;
  assigned_to?: string;
  limit?: number;
  cursor?: string;
}

export async function fetchReviewQueue(
  params?: ReviewQueueParams,
): Promise<{ items: ReviewItem[]; next_cursor?: string | null }> {
  const searchParams = new URLSearchParams();
  if (params?.status && params.status !== "all") {
    searchParams.set("status", params.status);
  }
  if (params?.assigned_to) {
    searchParams.set("assigned_to", params.assigned_to);
  }
  if (params?.limit) {
    searchParams.set("limit", String(params.limit));
  }
  if (params?.cursor) {
    searchParams.set("cursor", params.cursor);
  }

  const query = searchParams.toString();
  const endpoint = `/api/v1/reviews${query ? `?${query}` : ""}`;
  const response = await apiRequest(endpoint, ReviewListSchema);
  return {
    items: response.items as ReviewItem[],
    next_cursor: response.next_cursor,
  };
}

export async function fetchReviewItem(reviewId: string): Promise<ReviewItem> {
  const encodedId = encodeURIComponent(reviewId);
  const response = await apiRequest(`/api/v1/reviews/${encodedId}`, ReviewItemSchema);
  return response as ReviewItem;
}

export async function claimReviewItem(
  reviewId: string,
  expectedVersion: number,
): Promise<ReviewItem> {
  const encodedId = encodeURIComponent(reviewId);
  const response = await apiRequest(
    `/api/v1/reviews/${encodedId}/claim`,
    ReviewItemSchema,
    {
      method: "POST",
      body: JSON.stringify({ expected_version: expectedVersion }),
    },
  );
  return response as ReviewItem;
}

export async function reopenReviewItem(
  reviewId: string,
  expectedVersion: number,
  rationale: string,
): Promise<{ item: ReviewItem }> {
  const encodedId = encodeURIComponent(reviewId);
  const response = await apiRequest(
    `/api/v1/reviews/${encodedId}/reopen`,
    z.object({ item: ReviewItemSchema }),
    {
      method: "POST",
      body: JSON.stringify({
        expected_version: expectedVersion,
        rationale,
      }),
    },
  );
  return response as { item: ReviewItem };
}

export async function fetchGovernanceMetrics(): Promise<GovernanceMetrics> {
  const response = await apiRequest("/api/v1/reviews/metrics", GovernanceMetricsSchema);
  return response as GovernanceMetrics;
}
