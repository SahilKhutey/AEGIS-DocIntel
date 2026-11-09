import { z } from "zod";

export const JobStatusEnum = z.enum([
  "PENDING",
  "RUNNING",
  "COMPLETED",
  "FAILED",
  "CANCELLED",
  "RETRYING",
]);

export const JobResponseSchema = z.object({
  job_id: z.string().min(1),
  tenant_id: z.string().min(1),
  job_type: z.string().min(1),
  resource_id: z.string().min(1),
  status: JobStatusEnum,
  attempt: z.number().int().default(1),
  max_attempts: z.number().int().default(3),
  error_code: z.string().nullable().optional(),
  error_message: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const JobEventSchema = z.object({
  id: z.string().min(1),
  job_id: z.string().min(1),
  event_type: z.string().min(1),
  from_status: z.string().nullable().optional(),
  to_status: z.string(),
  payload: z.record(z.string(), z.unknown()).default({}),
  timestamp: z.string(),
});

export const JobListResponseSchema = z.object({
  items: z.array(JobResponseSchema),
  total: z.number().int().nonnegative(),
});

export type JobResponse = z.infer<typeof JobResponseSchema>;
export type JobEvent = z.infer<typeof JobEventSchema>;
export type JobListResponse = z.infer<typeof JobListResponseSchema>;
