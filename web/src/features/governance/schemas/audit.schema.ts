import { z } from "zod";

export const AuditEventSchema = z.object({
  event_id: z.string(),
  review_id: z.string(),
  sequence: z.number(),
  tenant_id: z.string(),
  actor_id: z.string(),
  action: z.string(),
  previous_status: z.string(),
  new_status: z.string(),
  previous_version: z.number(),
  new_version: z.number(),
  rationale: z.string(),
  revision_id: z.string().nullable().optional(),
  request_id: z.string().nullable().optional(),
  timestamp: z.string(),
});

export const AuditHistorySchema = z.array(AuditEventSchema);

export type AuditEvent = z.infer<typeof AuditEventSchema>;
export type AuditHistory = z.infer<typeof AuditHistorySchema>;
