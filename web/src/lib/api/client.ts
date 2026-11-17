import { z } from "zod";
import { ApiError } from "./errors";
import { getContextHeaders } from "./request-context";

const ApiErrorSchema = z.object({
  detail: z.union([z.string(), z.array(z.unknown()), z.record(z.string(), z.unknown())]).optional(),
  code: z.string().optional(),
  request_id: z.string().optional(),
});

export interface RequestOptions extends Omit<RequestInit, "headers"> {
  headers?: HeadersInit;
  workspaceId?: string;
  tenantId?: string;
  timeoutMs?: number;
}

export function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_AEGIS_API_URL;
    if (envUrl) {
      return envUrl.replace(/\/+$/, "");
    }
    // In browser runtime, default to same-origin relative URL to enable reverse proxy & rewrites
    return "";
  }
  // Server-side default to internal docker or configured backend URL
  return (
    process.env.INTERNAL_API_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.NEXT_PUBLIC_AEGIS_API_URL ||
    ""
  ).replace(/\/+$/, "");
}

export function getDefaultAuthHeaders(): Record<string, string> {
  // Check browser storage for an active session token
  if (typeof window !== "undefined") {
    try {
      const storedToken =
        sessionStorage.getItem("aegis_auth_token") || localStorage.getItem("aegis_auth_token");
      if (storedToken) {
        return { Authorization: `Bearer ${storedToken}` };
      }
    } catch {
      // Storage access blocked or restricted
    }
  }

  // Fail closed in production: do not send insecure default tokens
  return {};
}

export async function apiRequest<T>(
  path: string,
  schema?: z.ZodType<T>,
  options: RequestOptions = {}
): Promise<T> {
  if (!path.startsWith("/")) {
    throw new Error(`API path must be a relative path starting with '/', received '${path}'.`);
  }

  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${path}`;

  const {
    workspaceId,
    tenantId,
    headers: customHeaders,
    timeoutMs = 30000,
    ...fetchInit
  } = options;

  const isFormData = typeof FormData !== "undefined" && fetchInit.body instanceof FormData;
  const authHeaders = getDefaultAuthHeaders();
  const ctxHeaders = getContextHeaders();

  if (workspaceId) {
    ctxHeaders["X-Workspace-ID"] = workspaceId;
  }
  if (tenantId) {
    ctxHeaders["X-Tenant-ID"] = tenantId;
  }

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...authHeaders,
    ...ctxHeaders,
    ...(!isFormData ? { "Content-Type": "application/json" } : {}),
    ...(customHeaders instanceof Headers
      ? Object.fromEntries(customHeaders.entries())
      : Array.isArray(customHeaders)
        ? Object.fromEntries(customHeaders)
        : (customHeaders as Record<string, string> || {})),
  };

  // Setup abort controller for timeout handling
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...fetchInit,
      headers,
      credentials: "include",
      cache: "no-store",
      signal: fetchInit.signal || controller.signal,
    });

    if (!response.ok) {
      let errorDetail = `Request failed (${response.status})`;
      let code: string | undefined;
      let requestId: string | undefined;

      try {
        const body: unknown = await response.json();
        const parsed = ApiErrorSchema.safeParse(body);
        if (parsed.success) {
          if (parsed.data.detail) {
            errorDetail =
              typeof parsed.data.detail === "string"
                ? parsed.data.detail
                : JSON.stringify(parsed.data.detail);
          }
          code = parsed.data.code;
          requestId = parsed.data.request_id;
        }
      } catch {
        // Response was not JSON
      }

      throw new ApiError(errorDetail, response.status, code, requestId);
    }

    if (response.status === 204) {
      return (schema ? schema.parse(undefined) : undefined) as T;
    }

    const rawBody: unknown = await response.json();

    if (!schema) {
      return rawBody as T;
    }

    const parseResult = schema.safeParse(rawBody);
    if (!parseResult.success) {
      const issues = parseResult.error.issues
        .map((i) => `${i.path.join(".")}: ${i.message}`)
        .join(", ");
      throw new ApiError(
        `Response contract validation failed: ${issues}`,
        response.status,
        "SCHEMA_VALIDATION_ERROR",
        undefined,
        parseResult.error
      );
    }

    return parseResult.data;
  } finally {
    clearTimeout(timeoutId);
  }
}
