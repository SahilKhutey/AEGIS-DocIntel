import { apiRequest } from "@/lib/api-client";
import { AuditHistorySchema } from "../schemas/audit.schema";
import type { AuditEvent } from "../types";

export async function fetchReviewAuditHistory(reviewId: string): Promise<AuditEvent[]> {
  const encodedId = encodeURIComponent(reviewId);
  const response = await apiRequest(
    `/api/v1/reviews/${encodedId}/history`,
    AuditHistorySchema,
  );
  return response as AuditEvent[];
}
