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

// In-memory session cache
let cachedSession: UserSession | null = null;

function parseJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payloadBase64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const jsonStr =
      typeof window !== "undefined"
        ? decodeURIComponent(
            atob(payloadBase64)
              .split("")
              .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
              .join("")
          )
        : Buffer.from(payloadBase64, "base64").toString("utf-8");
    return JSON.parse(jsonStr);
  } catch {
    return null;
  }
}

export function resolveSessionFromToken(token: string): UserSession | null {
  if (!token) return null;

  // Development bypass token
  if (token.startsWith("dev-")) {
    const tenantId = token.slice(4) || "default-tenant";
    return {
      user: {
        id: "dev-user",
        email: "dev@aegis.corp",
        displayName: "AEGIS Developer",
      },
      workspaceId: `ws-${tenantId}`,
      tenantId,
      role: "admin",
      permissions: getPermissionsForRole("admin"),
      token,
      expiresAt: new Date(Date.now() + 86400000).toISOString(),
    };
  }

  // JWT parsing
  const payload = parseJwtPayload(token);
  if (!payload) return null;

  const tenantId = String(payload.tenant_id || payload.tid || "default-tenant");
  const userId = String(payload.sub || payload.user_id || "anonymous");
  const role = String(payload.role || "viewer");
  const exp = typeof payload.exp === "number" ? new Date(payload.exp * 1000).toISOString() : undefined;

  // Check expiration if exp is present
  if (typeof payload.exp === "number" && payload.exp * 1000 < Date.now()) {
    return null;
  }

  return {
    user: {
      id: userId,
      email: typeof payload.email === "string" ? payload.email : undefined,
      displayName: typeof payload.name === "string" ? payload.name : userId,
    },
    workspaceId: typeof payload.workspace_id === "string" ? payload.workspace_id : `ws-${tenantId}`,
    tenantId,
    role,
    permissions: getPermissionsForRole(role),
    expiresAt: exp,
    token,
  };
}

export const defaultSessionProvider: SessionProvider = {
  async getSession(): Promise<UserSession | null> {
    if (cachedSession) {
      if (cachedSession.expiresAt && new Date(cachedSession.expiresAt).getTime() < Date.now()) {
        cachedSession = null;
        return null;
      }
      return cachedSession;
    }

    const token =
      process.env.NEXT_PUBLIC_AEGIS_DEV_TOKEN ||
      (typeof window !== "undefined" ? window.sessionStorage.getItem("aegis_token") : null) ||
      "dev-default-tenant";

    cachedSession = resolveSessionFromToken(token);
    return cachedSession;
  },

  async refreshSession(): Promise<UserSession | null> {
    cachedSession = null;
    return this.getSession();
  },

  async signOut(): Promise<void> {
    cachedSession = null;
    clearRequestContext();
    if (typeof window !== "undefined") {
      window.sessionStorage.removeItem("aegis_token");
      window.localStorage.removeItem("aegis_cached_workspace");
    }
  },
};
