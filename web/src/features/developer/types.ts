export interface ApiKeyItem {
  id: string;
  name: string;
  prefix: string; // e.g. "aegis_live_****3fa9"
  scopes: string[];
  createdAt: string;
  lastUsedAt?: string | null;
  expiresAt?: string | null;
}

export interface CreatedApiKeyResult {
  key: ApiKeyItem;
  secret: string; // Only displayed once on creation
}

export interface WebhookSubscription {
  id: string;
  url: string;
  events: string[];
  isActive: boolean;
  secretTokenHint: string;
  createdAt: string;
  lastDeliveredAt?: string | null;
  failureCount: number;
}

export interface WebhookDeliveryLog {
  id: string;
  subscriptionId: string;
  event: string;
  statusCode: number;
  durationMs: number;
  timestamp: string;
  payload: Record<string, unknown>;
  responseBody?: string;
  success: boolean;
}

export interface IntegrationConnector {
  id: string;
  name: string;
  category: "storage" | "database" | "identity" | "llm" | "messaging";
  provider: string;
  status: "connected" | "degraded" | "disconnected";
  endpoint: string;
  lastVerifiedAt: string;
  latencyMs: number;
}

export interface OpenApiEndpoint {
  path: string;
  method: "GET" | "POST" | "DELETE" | "PUT" | "PATCH";
  tag: string;
  summary: string;
  description?: string;
  parameters?: {
    name: string;
    in: "query" | "path" | "header";
    required: boolean;
    type: string;
    description?: string;
  }[];
  requestBodySample?: Record<string, unknown>;
  responseSample?: unknown;
}
