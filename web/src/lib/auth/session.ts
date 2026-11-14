import { z } from "zod";
import { Permission, getPermissionsForRole } from "./permissions";
import { clearRequestContext } from "../api/request-context";

export interface UserSession {
  user: {
    id: string;
    email?: string;
    displayName?: string;
  };
  workspaceId: string;
  tenantId: string;
  role: string;
  permissions: Permission[];
  expiresAt?: string;
  token?: string;
}

export interface SessionProvider {
  getSession(): Promise<UserSession | null>;
  refreshSession(): Promise<UserSession | null>;
  signOut(): Promise<void>;
}

export const GatewaySessionSchema = z.object({
  user_id: z.string().min(1).optional(),
  license_id: z.string().optional(),
  device_id: z.string().optional(),
  tier: z.string().optional(),
  role: z.string().default("viewer"),
  authenticated: z.boolean().optional(),
  user: z
    .object({
      id: z.string().min(1),
      email: z.string().optional(),
      displayName: z.string().optional(),
    })
    .optional(),
  workspaceId: z.string().optional(),
  tenantId: z.string().optional(),
  permissions: z.array(z.string()).optional(),
  expiresAt: z.string().optional(),
});

export function validateSessionResponse(data: unknown): UserSession {
  const parsed = GatewaySessionSchema.parse(data);
  const userId = parsed.user?.id || parsed.user_id || "evaluator";
  const tenantId = parsed.tenantId || parsed.license_id || "evaluator-workspace";
  const workspaceId = parsed.workspaceId || `ws-${tenantId}`;
  const role = parsed.role || "viewer";
  const perms = (parsed.permissions as Permission[]) || getPermissionsForRole(role);

  return {
    user: {
      id: userId,
      email: parsed.user?.email,
      displayName: parsed.user?.displayName || `Evaluator (${userId})`,
    },
    workspaceId,
    tenantId,
    role,
    permissions: perms,
    expiresAt: parsed.expiresAt,
  };
}

/**
 * Historical helper: strictly fails closed in hardened production model.
 * The browser never manufactures or verifies identity claims locally.
 */
export function resolveSessionFromToken(_token: string): UserSession | null {
  // Fail closed unconditionally: client-side token parsing does not verify signatures
  // and dev-* credentials are prohibited in the production authentication contract.
  return null;
}

export const defaultSessionProvider: SessionProvider = {
  async getSession(): Promise<UserSession | null> {
    if (typeof window === "undefined") {
      return null;
    }

    try {
      const response = await fetch("/evaluation/session", {
        method: "GET",
        credentials: "include",
        cache: "no-store",
        headers: { Accept: "application/json" },
      });

      if (response.status === 401 || response.status === 403 || response.status === 404) {
        return null;
      }
      if (!response.ok) {
        throw new Error("Unable to retrieve evaluation session");
      }

      const body = await response.json();
      return validateSessionResponse(body);
    } catch {
      return null;
    }
  },

  async refreshSession(): Promise<UserSession | null> {
    if (typeof window === "undefined") {
      return null;
    }

    try {
      const response = await fetch("/evaluation/session/refresh", {
        method: "POST",
        credentials: "include",
        cache: "no-store",
        headers: { Accept: "application/json" },
      });

      if (response.status === 401 || response.status === 403) {
        return null;
      }
      if (!response.ok) {
        throw new Error("Unable to refresh evaluation session");
      }

      const body = await response.json();
      return validateSessionResponse(body);
    } catch {
      return null;
    }
  },

  async signOut(): Promise<void> {
    try {
      if (typeof window !== "undefined") {
        await fetch("/evaluation/session/logout", {
          method: "POST",
          credentials: "include",
          cache: "no-store",
        });
      }
    } finally {
      clearRequestContext();
      if (typeof window !== "undefined") {
        window.sessionStorage.removeItem("aegis_token");
        window.sessionStorage.removeItem("aegis_auth_token");
        window.localStorage.removeItem("aegis_cached_workspace");
      }
    }
  },
};
