import { z } from "zod";
import { ApiError } from "./errors";

const ApiErrorSchema = z.object({
  detail: z.union([z.string(), z.array(z.unknown()), z.record(z.string(), z.unknown())]).optional(),
  code: z.string().optional(),
  request_id: z.string().optional(),
});

export function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    // Client-side: use configured env var or default to backend port 8000
    const envUrl = process.env.NEXT_PUBLIC_AEGIS_API_URL;
    if (envUrl) {
      return envUrl.replace(/\/+$/, "");
    }
    return "http://127.0.0.1:8000";
  }
  // Server-side
  return process.env.NEXT_PUBLIC_AEGIS_API_URL?.replace(/\/+$/, "") || "http://127.0.0.1:8000";
}

export function getDefaultAuthHeaders(): Record<string, string> {
  // Use development bypass token if configured, default to dev-default-tenant
  const devToken = process.env.NEXT_PUBLIC_AEGIS_DEV_TOKEN || "dev-default-tenant";
  return {
    Authorization: `Bearer ${devToken}`,
  };
}

export async function apiRequest<T>(
  path: string,
  schema: z.ZodType<T>,
  init: RequestInit = {},
): Promise<T> {
  if (!path.startsWith("/") || path.startsWith("//")) {
    throw new Error(`API path must be a relative path starting with '/', received '${path}'.`);
  }

  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${path}`;

  const isFormData = typeof FormData !== "undefined" && init.body instanceof FormData;
  const defaultHeaders = getDefaultAuthHeaders();

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...defaultHeaders,
    ...(!isFormData ? { "Content-Type": "application/json" } : {}),
    ...(init.headers as Record<string, string> || {}),
  };

  const response = await fetch(url, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    let errorDetail = `Request failed (${response.status})`;
    let requestId: string | undefined;

    try {
      const body: unknown = await response.json();
      const parsed = ApiErrorSchema.safeParse(body);
      if (parsed.success && parsed.data.detail) {
        errorDetail = typeof parsed.data.detail === "string"
          ? parsed.data.detail
          : JSON.stringify(parsed.data.detail);
      }
      if (parsed.success && parsed.data.request_id) {
        requestId = parsed.data.request_id;
      }
    } catch {
      // Body was not JSON
    }

    throw new ApiError(errorDetail, response.status, requestId);
  }

  // If response is 204 No Content
  if (response.status === 204) {
    return schema.parse(undefined);
  }

  const rawBody: unknown = await response.json();
  const parseResult = schema.safeParse(rawBody);

  if (!parseResult.success) {
    const issues = parseResult.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`).join(", ");
    throw new ApiError(
      `Response contract validation failed: ${issues}`,
      response.status,
      undefined,
      parseResult.error,
    );
  }

  return parseResult.data;
}
