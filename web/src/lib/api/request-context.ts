/**
 * Request context management for AEGIS-DocIntel
 * Injects tenant context, active workspace, and correlation headers into API requests.
 */

export interface RequestContext {
  workspaceId?: string;
  tenantId?: string;
  correlationId?: string;
}

let currentContext: RequestContext = {
  workspaceId: "workspace-default",
  tenantId: "default-tenant",
};

export function setRequestContext(ctx: Partial<RequestContext>): void {
  currentContext = {
    ...currentContext,
    ...ctx,
  };
}

export function getRequestContext(): RequestContext {
  return { ...currentContext };
}

export function clearRequestContext(): void {
  currentContext = {
    workspaceId: "workspace-default",
    tenantId: "default-tenant",
  };
}

export function getContextHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  if (currentContext.workspaceId) {
    headers["X-Workspace-ID"] = currentContext.workspaceId;
  }
  if (currentContext.tenantId) {
    headers["X-Tenant-ID"] = currentContext.tenantId;
  }
  if (currentContext.correlationId) {
    headers["X-Correlation-ID"] = currentContext.correlationId;
  }
  return headers;
}
