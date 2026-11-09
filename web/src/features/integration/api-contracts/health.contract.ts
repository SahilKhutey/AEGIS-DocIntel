import { z } from "zod";

export const HealthLiveResponseSchema = z.object({
  status: z.literal("ok"),
});

export const HealthReadyResponseSchema = z.object({
  status: z.enum(["ok", "degraded", "unavailable"]),
  dependencies: z.record(
    z.string(),
    z.object({
      status: z.enum(["healthy", "degraded", "unhealthy"]),
      latency_ms: z.number().optional(),
      message: z.string().optional(),
    })
  ).optional(),
});

export type HealthLiveResponse = z.infer<typeof HealthLiveResponseSchema>;
export type HealthReadyResponse = z.infer<typeof HealthReadyResponseSchema>;
