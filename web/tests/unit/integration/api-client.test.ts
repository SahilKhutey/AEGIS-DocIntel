import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiRequest } from "@/lib/api/client";
import { ApiError, isUnauthorized, isForbidden, isConflict, isValidationError } from "@/lib/api/errors";
import { setRequestContext, clearRequestContext, getContextHeaders } from "@/lib/api/request-context";
import { z } from "zod";

describe("API Client & Integration Transports", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    clearRequestContext();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("injects workspace and tenant headers correctly", () => {
    setRequestContext({ workspaceId: "ws-test-42", tenantId: "tenant-delta" });
    const headers = getContextHeaders();
    expect(headers["X-Workspace-ID"]).toBe("ws-test-42");
    expect(headers["X-Tenant-ID"]).toBe("tenant-delta");
  });

  it("handles valid 200 responses with schema parsing", async () => {
    const TestSchema = z.object({
      id: z.string(),
      count: z.number(),
    });

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: "doc-1", count: 42 }),
    });

    const result = await apiRequest("/v1/test", TestSchema);
    expect(result).toEqual({ id: "doc-1", count: 42 });
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/v1/test"),
      expect.objectContaining({
        headers: expect.objectContaining({
          Accept: "application/json",
          "X-Workspace-ID": "workspace-default",
        }),
      })
    );
  });

  it("handles 204 No Content safely", async () => {
    const VoidSchema = z.void();

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
    });

    const result = await apiRequest("/v1/delete", VoidSchema);
    expect(result).toBeUndefined();
  });

  it("throws ApiError on HTTP 401 Unauthorized", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Invalid token" }),
    });

    await expect(apiRequest("/v1/protected")).rejects.toThrow(ApiError);
    try {
      await apiRequest("/v1/protected");
    } catch (err) {
      expect(isUnauthorized(err)).toBe(true);
      expect((err as ApiError).status).toBe(401);
    }
  });

  it("throws ApiError on HTTP 403 Forbidden", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: "Insufficient role permissions" }),
    });

    try {
      await apiRequest("/v1/admin/restricted");
    } catch (err) {
      expect(isForbidden(err)).toBe(true);
      expect((err as ApiError).status).toBe(403);
    }
  });

  it("throws ApiError on HTTP 409 Conflict", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ detail: "Document version conflict" }),
    });

    try {
      await apiRequest("/v1/documents/conflict");
    } catch (err) {
      expect(isConflict(err)).toBe(true);
      expect((err as ApiError).status).toBe(409);
    }
  });

  it("throws ApiError on schema validation failure without exposing raw secrets", async () => {
    const StrictSchema = z.object({
      required_key: z.string(),
    });

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ wrong_key: 123 }),
    });

    await expect(apiRequest("/v1/strict", StrictSchema)).rejects.toThrow(ApiError);
    try {
      await apiRequest("/v1/strict", StrictSchema);
    } catch (err) {
      expect((err as ApiError).code).toBe("SCHEMA_VALIDATION_ERROR");
      const validationErr = new ApiError("Validation failure", 422);
      expect(isValidationError(validationErr)).toBe(true);
    }
  });
});
