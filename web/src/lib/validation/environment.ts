import { z } from "zod";

const PublicEnvironmentSchema = z.object({
  NEXT_PUBLIC_API_BASE_URL: z.string().url().optional(),
  NEXT_PUBLIC_AEGIS_API_URL: z.string().url().optional(),
  NEXT_PUBLIC_APP_ENV: z
    .enum(["development", "test", "staging", "production"])
    .default("development"),
  NEXT_PUBLIC_AEGIS_DEV_TOKEN: z.string().optional(),
});

export type PublicEnvironment = z.infer<typeof PublicEnvironmentSchema>;

export function validatePublicEnvironment(env: Record<string, string | undefined> = process.env): PublicEnvironment {
  const parsed = PublicEnvironmentSchema.safeParse({
    NEXT_PUBLIC_API_BASE_URL: env.NEXT_PUBLIC_API_BASE_URL,
    NEXT_PUBLIC_AEGIS_API_URL: env.NEXT_PUBLIC_AEGIS_API_URL,
    NEXT_PUBLIC_APP_ENV: env.NEXT_PUBLIC_APP_ENV || "development",
    NEXT_PUBLIC_AEGIS_DEV_TOKEN: env.NEXT_PUBLIC_AEGIS_DEV_TOKEN,
  });

  if (!parsed.success) {
    const issues = parsed.error.issues
      .map((i) => `${i.path.join(".")}: ${i.message}`)
      .join(", ");
    throw new Error(`Environment validation failed: ${issues}`);
  }

  return parsed.data;
}

export const publicEnvironment = validatePublicEnvironment();
