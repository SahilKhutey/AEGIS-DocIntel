import {
  type ApiKeyItem,
  type CreatedApiKeyResult,
  type WebhookSubscription,
  type WebhookDeliveryLog,
  type IntegrationConnector,
  type OpenApiEndpoint,
} from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let IN_MEMORY_KEYS: ApiKeyItem[] = [
  {
    id: "key-live-01",
    name: "Production Ingestion Pipeline",
    prefix: "aegis_live_****3fa9",
    scopes: ["documents.read", "documents.upload", "processing.read"],
    createdAt: "2026-10-15T09:00:00.000Z",
    lastUsedAt: "2026-11-09T08:15:00.000Z",
  },
  {
    id: "key-live-02",
    name: "Read-Only Intelligence Dashboard",
    prefix: "aegis_live_****8b12",
    scopes: ["workspace.read", "intelligence.query", "evidence.read"],
    createdAt: "2026-10-28T14:30:00.000Z",
    lastUsedAt: "2026-11-09T10:04:00.000Z",
  },
];

let IN_MEMORY_WEBHOOKS: WebhookSubscription[] = [
  {
    id: "sub-wh-01",
    url: "https://api.enterprise-corp.com/hooks/aegis-events",
    events: ["document.completed", "job.failed"],
    isActive: true,
    secretTokenHint: "whsec_****7a4f",
    createdAt: "2026-11-01T12:00:00.000Z",
    lastDeliveredAt: "2026-11-09T08:15:42.000Z",
    failureCount: 0,
  },
  {
    id: "sub-wh-02",
    url: "https://compliance.internal.bank/aegis/review-audit",
    events: ["governance.review_required", "governance.decision_submitted"],
    isActive: true,
    secretTokenHint: "whsec_****91c0",
    createdAt: "2026-11-05T16:20:00.000Z",
    lastDeliveredAt: "2026-11-09T07:45:10.000Z",
    failureCount: 0,
  },
];

const MOCK_DELIVERY_LOGS: WebhookDeliveryLog[] = [
  {
    id: "log-del-01",
    subscriptionId: "sub-wh-01",
    event: "document.completed",
    statusCode: 200,
    durationMs: 142,
    timestamp: "2026-11-09T08:15:42.000Z",
    success: true,
    payload: {
      event: "document.completed",
      document_id: "doc-sample-01",
      chunks: 24,
      status: "ready",
    },
    responseBody: '{"status":"received","ack":true}',
  },
  {
    id: "log-del-02",
    subscriptionId: "sub-wh-01",
    event: "job.failed",
    statusCode: 200,
    durationMs: 98,
    timestamp: "2026-11-09T07:12:30.000Z",
    success: true,
    payload: {
      event: "job.failed",
      job_id: "job-run-9023",
      error_code: "OCR_TIMEOUT_EXCEEDED",
    },
    responseBody: '{"status":"alert_dispatched"}',
  },
];

const MOCK_CONNECTORS: IntegrationConnector[] = [
  {
    id: "conn-s3",
    name: "Amazon S3 Document Lake",
    category: "storage",
    provider: "AWS S3 / Cloudflare R2",
    status: "connected",
    endpoint: "s3://aegis-enterprise-vault-us-east-1",
    lastVerifiedAt: "2026-11-09T10:00:00.000Z",
    latencyMs: 38,
  },
  {
    id: "conn-postgres",
    name: "Relational Knowledge DB",
    category: "database",
    provider: "PostgreSQL 16",
    status: "connected",
    endpoint: "postgres.cluster.internal:5432/aegis_docintel",
    lastVerifiedAt: "2026-11-09T10:00:00.000Z",
    latencyMs: 4,
  },
  {
    id: "conn-qdrant",
    name: "Vector Search Cluster",
    category: "database",
    provider: "Qdrant Distributed",
    status: "connected",
    endpoint: "https://vector-db.aegis.internal:6333",
    lastVerifiedAt: "2026-11-09T10:00:00.000Z",
    latencyMs: 18,
  },
  {
    id: "conn-auth",
    name: "Enterprise Identity & SSO",
    category: "identity",
    provider: "OIDC / Okta",
    status: "connected",
    endpoint: "https://auth.enterprise-corp.com/oauth2/v1",
    lastVerifiedAt: "2026-11-09T09:45:00.000Z",
    latencyMs: 54,
  },
];

export const OPENAPI_ENDPOINTS: OpenApiEndpoint[] = [
  {
    path: "/v1/admin/stats",
    method: "GET",
    tag: "Admin & Observability",
    summary: "Retrieve tenant statistics and operational metrics",
    description: "Returns aggregated document counts, chunk counts, token usage, cost, and query latency.",
    responseSample: {
      doc_count: 78,
      chunk_count: 1850,
      total_tokens_used: 742000,
      total_cost_usd: 11.13,
      cache_hit_rate: 64.2,
      avg_query_latency_ms: 196,
    },
  },
  {
    path: "/v1/jobs",
    method: "GET",
    tag: "Pipeline Execution",
    summary: "List background processing jobs",
    description: "Returns list of processing pipeline runs with filtering by status and pagination.",
    parameters: [
      { name: "status", in: "query", required: false, type: "string", description: "Filter by job status" },
      { name: "limit", in: "query", required: false, type: "integer", description: "Results per page" },
    ],
    responseSample: {
      items: [{ job_id: "job-run-9021", status: "completed", attempt: 1 }],
      total: 1,
    },
  },
  {
    path: "/v1/jobs/{job_id}/retry",
    method: "POST",
    tag: "Pipeline Execution",
    summary: "Retry a failed pipeline execution",
    parameters: [
      { name: "job_id", in: "path", required: true, type: "string", description: "Pipeline Job ID" },
    ],
    responseSample: { success: true, message: "Job queued for retry" },
  },
  {
    path: "/v1/webhooks/subscriptions",
    method: "GET",
    tag: "Webhooks",
    summary: "List active webhook subscriptions",
    responseSample: [{ id: "sub-wh-01", url: "https://api.enterprise.com/hooks" }],
  },
  {
    path: "/v1/webhooks/subscriptions",
    method: "POST",
    tag: "Webhooks",
    summary: "Register new webhook subscription with SSRF verification",
    requestBodySample: {
      url: "https://api.enterprise.com/hooks/aegis",
      events: ["document.completed", "job.failed"],
    },
    responseSample: { id: "sub-wh-new", url: "https://api.enterprise.com/hooks/aegis", isActive: true },
  },
  {
    path: "/v1/advanced/math/unified-evaluation",
    method: "POST",
    tag: "Advanced Mathematics",
    summary: "Execute mathematical expression evaluation",
    requestBodySample: {
      expression: "cos_sim(u, v) * 0.85 + bm25 * 0.15",
      variables: { bm25: 14.2 },
    },
    responseSample: { result: 0.8654, evaluatedAt: "2026-11-09T10:00:00.000Z" },
  },
];

export async function getApiKeys(): Promise<ApiKeyItem[]> {
  return [...IN_MEMORY_KEYS];
}

export async function createApiKey(
  name: string,
  scopes: string[],
): Promise<CreatedApiKeyResult> {
  const randomSuffix = Math.random().toString(36).substring(2, 6);
  const secret = `aegis_live_sec_${Math.random().toString(36).substring(2, 18)}${Math.random().toString(36).substring(2, 18)}`;
  const key: ApiKeyItem = {
    id: `key-live-${Date.now()}`,
    name,
    prefix: `aegis_live_****${randomSuffix}`,
    scopes,
    createdAt: new Date().toISOString(),
    lastUsedAt: null,
  };
  IN_MEMORY_KEYS = [key, ...IN_MEMORY_KEYS];
  return { key, secret };
}

export async function revokeApiKey(id: string): Promise<boolean> {
  IN_MEMORY_KEYS = IN_MEMORY_KEYS.filter((k) => k.id !== id);
  return true;
}

export async function getWebhookSubscriptions(): Promise<WebhookSubscription[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/v1/webhooks/subscriptions`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch {
    return [...IN_MEMORY_WEBHOOKS];
  }
}

export async function createWebhookSubscription(
  url: string,
  events: string[],
): Promise<WebhookSubscription> {
  try {
    const res = await fetch(`${API_BASE_URL}/v1/webhooks/subscriptions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, events }),
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch {
    const newSub: WebhookSubscription = {
      id: `sub-wh-${Date.now()}`,
      url,
      events,
      isActive: true,
      secretTokenHint: `whsec_****${Math.random().toString(36).substring(2, 6)}`,
      createdAt: new Date().toISOString(),
      lastDeliveredAt: null,
      failureCount: 0,
    };
    IN_MEMORY_WEBHOOKS = [newSub, ...IN_MEMORY_WEBHOOKS];
    return newSub;
  }
}

export async function deleteWebhookSubscription(id: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/v1/webhooks/subscriptions/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
  } catch {
    IN_MEMORY_WEBHOOKS = IN_MEMORY_WEBHOOKS.filter((w) => w.id !== id);
  }
  return true;
}

export async function getWebhookDeliveryLogs(): Promise<WebhookDeliveryLog[]> {
  return [...MOCK_DELIVERY_LOGS];
}

export async function getIntegrationConnectors(): Promise<IntegrationConnector[]> {
  return [...MOCK_CONNECTORS];
}
