"use client";

import React, { createContext, useContext, useMemo } from "react";
import type { Permission } from "@/config/permissions";
import { canAccess, type AccessDecision, type AccessContext as CoreAccessContext } from "./access-policy";

interface AccessContextValue extends CoreAccessContext {
  checkAccess: (required: readonly Permission[], mode?: "all" | "any") => AccessDecision;
}

const AccessContext = createContext<AccessContextValue>({
  isAuthenticated: true,
  permissions: [
    "workspace.read",
    "documents.read",
    "documents.upload",
    "documents.compare",
    "processing.read",
    "intelligence.query",
    "governance.read",
    "evidence.read",
  ],
  checkAccess: () => ({ allowed: true }),
});

export interface AccessProviderProps {
  children: React.ReactNode;
  isAuthenticated?: boolean;
  permissions?: readonly Permission[];
}

export function AccessProvider({
  children,
  isAuthenticated = true,
  permissions = [
    "workspace.read",
    "documents.read",
    "documents.upload",
    "documents.compare",
    "processing.read",
    "intelligence.query",
    "governance.read",
    "evidence.read",
  ],
}: AccessProviderProps) {
  const value = useMemo<AccessContextValue>(() => {
    const ctx: CoreAccessContext = { isAuthenticated, permissions };
    return {
      isAuthenticated,
      permissions,
      checkAccess: (required, mode = "all") => canAccess(ctx, required, mode),
    };
  }, [isAuthenticated, permissions]);

  return <AccessContext.Provider value={value}>{children}</AccessContext.Provider>;
}

export function useAccess() {
  return useContext(AccessContext);
}

export interface RequirePermissionProps {
  permissions: readonly Permission[];
  mode?: "all" | "any";
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function RequirePermission({
  permissions,
  mode = "all",
  children,
  fallback = null,
}: RequirePermissionProps) {
  const { checkAccess } = useAccess();
  const decision = checkAccess(permissions, mode);

  if (!decision.allowed) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
