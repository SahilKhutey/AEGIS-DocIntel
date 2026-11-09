import { z } from "zod";

export const RealtimeEventSchema = z.object({
  eventId: z.string().min(1),
  type: z.string().min(1),
  workspaceId: z.string().min(1),
  occurredAt: z.string().datetime({ offset: true }),
  sequence: z.number().int().nonnegative().optional(),
  entityId: z.string().optional(),
  payload: z.record(z.string(), z.unknown()),
});

export type RealtimeEvent = z.infer<typeof RealtimeEventSchema>;

export const EVENT_TYPES = [
  "document.processing.started",
  "document.processing.progress",
  "document.processing.completed",
  "document.processing.failed",
  "pipeline.stage.started",
  "pipeline.stage.completed",
  "pipeline.run.failed",
  "governance.review.assigned",
  "governance.decision.submitted",
  "monitoring.alert.raised",
  "monitoring.alert.resolved",
  "notification.created",
] as const;

export type EventType = (typeof EVENT_TYPES)[number];
