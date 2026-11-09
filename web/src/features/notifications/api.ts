import { z } from "zod";
import type { NotificationListResponse } from "./types";
import { apiRequest } from "@/lib/api-client";

export const NotificationSchema = z.object({
  id: z.string(),
  type: z.enum([
    "processing",
    "intelligence",
    "evidence",
    "governance",
    "system",
    "security",
  ]),
  title: z.string(),
  message: z.string(),
  createdAt: z.string(),
  readAt: z.string().nullable(),
  resourceUrl: z.string().optional(),
});

export const NotificationListResponseSchema = z.object({
  items: z.array(NotificationSchema),
  unreadCount: z.number(),
  nextCursor: z.string().optional(),
});

export interface NotificationService {
  list(input?: { cursor?: string; limit?: number }): Promise<NotificationListResponse>;
  markRead(id: string): Promise<void>;
  markAllRead(): Promise<void>;
}

export class DefaultNotificationService implements NotificationService {
  async list(input?: { cursor?: string; limit?: number }): Promise<NotificationListResponse> {
    const params = new URLSearchParams();
    if (input?.cursor) params.set("cursor", input.cursor);
    if (input?.limit) params.set("limit", String(input.limit));

    const query = params.toString() ? `?${params.toString()}` : "";
    return await apiRequest(`/api/v1/notifications${query}`, NotificationListResponseSchema);
  }

  async markRead(id: string): Promise<void> {
    await apiRequest(`/api/v1/notifications/${encodeURIComponent(id)}/read`, z.object({ success: z.boolean() }), {
      method: "POST",
    });
  }

  async markAllRead(): Promise<void> {
    await apiRequest("/api/v1/notifications/read-all", z.object({ success: z.boolean() }), {
      method: "POST",
    });
  }
}

export const notificationService = new DefaultNotificationService();
