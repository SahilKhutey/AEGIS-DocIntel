import axios, { AxiosInstance } from "axios";
import FormData from "form-data";
import {
  AmdiError,
  AmdiAuthError,
  AmdiNotFoundError,
  AmdiRateLimitError,
  AmdiServerError,
  AmdiValidationError,
} from "./exceptions";
import * as models from "./models";

export class AmdiClient {
  private client: AxiosInstance;
  public documents: DocumentsAPI;
  public retrieval: RetrievalAPI;
  public context: ContextAPI;
  public export: ExportAPI;
  public agents: AgentsAPI;
  public verification: VerificationAPI;
  public engines: EnginesAPI;
  public memory: MemoryAPI;
  public dashboards: DashboardsAPI;

  constructor(
    private apiKey: string,
    private baseUrl: string = "https://api.amdi-os.com",
    private timeout: number = 60000
  ) {
    if (!apiKey) {
      throw new Error("apiKey is required");
    }
    this.client = axios.create({
      baseURL: baseUrl.replace(/\/+$/, ""),
      timeout: timeout,
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "User-Agent": "amdi-os-typescript-sdk/1.0.0",
        "Content-Type": "application/json",
      },
    });

    this.documents = new DocumentsAPI(this);
    this.retrieval = new RetrievalAPI(this);
    this.context = new ContextAPI(this);
    this.export = new ExportAPI(this);
    this.agents = new AgentsAPI(this);
    this.verification = new VerificationAPI(this);
    this.engines = new EnginesAPI(this);
    this.memory = new MemoryAPI(this);
    this.dashboards = new DashboardsAPI(this);
  }

  public async request<T = any>(config: {
    method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
    url: string;
    params?: any;
    data?: any;
    headers?: any;
  }): Promise<T> {
    try {
      const response = await this.client.request(config);
      return response.data;
    } catch (error: any) {
      if (axios.isAxiosError(error) && error.response) {
        const status = error.response.status;
        const errorData = error.response.data || {};
        const message = errorData.message || `HTTP ${status}`;

        if (status === 401 || status === 403) {
          throw new AmdiAuthError(message, status, errorData);
        }
        if (status === 404) {
          throw new AmdiNotFoundError(message, status, errorData);
        }
        if (status === 429) {
          const retryAfter = error.response.headers["retry-after"];
          throw new AmdiRateLimitError(
            message,
            retryAfter ? parseInt(retryAfter, 10) : undefined,
            status,
            errorData
          );
        }
        if (status >= 400 && status < 500) {
          throw new AmdiValidationError(message, status, errorData);
        }
        if (status >= 500) {
          throw new AmdiServerError(message, status, errorData);
        }
        throw new AmdiError(message, status, errorData);
      }
      throw new AmdiError(error.message || "Unknown network error");
    }
  }
}

export class DocumentsAPI {
  constructor(private client: AmdiClient) {}

  public async upload(
    fileStreamOrBuffer: any,
    filename: string,
    tags?: string[],
    metadata?: Record<string, any>
  ): Promise<models.DocumentSummary> {
    const form = new FormData();
    form.append("file", fileStreamOrBuffer, filename);
    if (tags) {
      form.append("tags", JSON.stringify(tags));
    }
    if (metadata) {
      form.append("metadata", JSON.stringify(metadata));
    }

    return this.client.request<models.DocumentSummary>({
      method: "POST",
      url: "/api/v1/documents",
      data: form,
      headers: form.getHeaders
        ? form.getHeaders()
        : { "Content-Type": "multipart/form-data" },
    });
  }

  public async get(documentId: string): Promise<models.Document> {
    return this.client.request<models.Document>({
      method: "GET",
      url: `/api/v1/documents/${documentId}`,
    });
  }

  public async list(params?: {
    tag?: string;
    file_type?: string;
    limit?: number;
    offset?: number;
  }): Promise<models.DocumentSummary[]> {
    return this.client.request<models.DocumentSummary[]>({
      method: "GET",
      url: "/api/v1/documents",
      params: params,
    });
  }

  public async delete(documentId: string): Promise<void> {
    return this.client.request<void>({
      method: "DELETE",
      url: `/api/v1/documents/${documentId}`,
    });
  }

  public async process(
    documentId: string,
    engines?: string[]
  ): Promise<Record<string, models.EngineOutput>> {
    const payload: any = { document_id: documentId };
    if (engines) {
      payload.engines = engines;
    }
    const response = await this.client.request({
      method: "POST",
      url: `/api/v1/documents/${documentId}/process`,
      data: payload,
    });
    const outputs = response.outputs || {};
    const result: Record<string, models.EngineOutput> = {};
    for (const key of Object.keys(outputs)) {
      result[key] = outputs[key] as models.EngineOutput;
    }
    return result;
  }
}

export class RetrievalAPI {
  constructor(private client: AmdiClient) {}

  public async search(
    query: string,
    params?: {
      top_k?: number;
      weights?: Record<string, number>;
      target_levels?: number[];
      include_snippets?: boolean;
    }
  ): Promise<models.RetrievalResult> {
    const data = {
      query: query,
      ...params,
    };
    return this.client.request<models.RetrievalResult>({
      method: "POST",
      url: "/api/v1/search",
      data: data,
    });
  }
}

export class ContextAPI {
  constructor(private client: AmdiClient) {}

  public async build(
    candidates: any[],
    totalBudget: number = 4000,
    options?: {
      citations?: any[];
      metadata?: Record<string, any>;
    }
  ): Promise<models.UniversalExportObject> {
    const data = {
      candidates: candidates,
      total_budget: totalBudget,
      ...options,
    };
    const response = await this.client.request({
      method: "POST",
      url: "/api/v1/context",
      data: data,
    });
    return response.ueo as models.UniversalExportObject;
  }
}

export class ExportAPI {
  constructor(private client: AmdiClient) {}

  public toJson(ueo: models.UniversalExportObject): string {
    return JSON.stringify(ueo, null, 2);
  }

  public async toMarkdown(ueo: models.UniversalExportObject): Promise<string> {
    return this.client.request<string>({
      method: "POST",
      url: "/api/v1/export/markdown",
      data: ueo,
    });
  }

  public async toYaml(ueo: models.UniversalExportObject): Promise<string> {
    return this.client.request<string>({
      method: "POST",
      url: "/api/v1/export/yaml",
      data: ueo,
    });
  }
}

export class AgentsAPI {
  public chatgpt: ChatGPTAPI;
  public gemini: GeminiAPI;
  public claude: ClaudeAPI;
  public deepseek: DeepSeekAPI;
  public qwen: QwenAPI;
  public local: LocalAPI;

  constructor(private client: AmdiClient) {
    this.chatgpt = new ChatGPTAPI(client);
    this.gemini = new GeminiAPI(client);
    this.claude = new ClaudeAPI(client);
    this.deepseek = new DeepSeekAPI(client);
    this.qwen = new QwenAPI(client);
    this.local = new LocalAPI(client);
  }

  public async listAgents(): Promise<any[]> {
    return this.client.request<any[]>({
      method: "GET",
      url: "/api/v1/agents",
    });
  }

  public async send(
    agent: string,
    ueo: models.UniversalExportObject,
    question?: string,
    options?: Record<string, any>
  ): Promise<models.ConnectorResponse> {
    const data = {
      ueo: ueo,
      question: question,
      ...options,
    };
    return this.client.request<models.ConnectorResponse>({
      method: "POST",
      url: `/api/v1/agents/${agent}/send`,
      data: data,
    });
  }
}

export class ChatGPTAPI {
  constructor(private client: AmdiClient) {}
  public async sendUeo(
    ueo: models.UniversalExportObject,
    question?: string,
    options?: { model?: string; temperature?: number; max_tokens?: number }
  ): Promise<models.ConnectorResponse> {
    return new AgentsAPI(this.client).send("chatgpt", ueo, question, options);
  }
}

export class GeminiAPI {
  constructor(private client: AmdiClient) {}
  public async sendUeo(
    ueo: models.UniversalExportObject,
    question?: string,
    options?: { model?: string; temperature?: number; max_tokens?: number }
  ): Promise<models.ConnectorResponse> {
    return new AgentsAPI(this.client).send("gemini", ueo, question, options);
  }
}

export class ClaudeAPI {
  constructor(private client: AmdiClient) {}
  public async sendUeo(
    ueo: models.UniversalExportObject,
    question?: string,
    options?: { model?: string; temperature?: number; max_tokens?: number }
  ): Promise<models.ConnectorResponse> {
    return new AgentsAPI(this.client).send("claude", ueo, question, options);
  }
}

export class DeepSeekAPI {
  constructor(private client: AmdiClient) {}
  public async sendUeo(
    ueo: models.UniversalExportObject,
    question?: string,
    options?: { model?: string; temperature?: number; max_tokens?: number }
  ): Promise<models.ConnectorResponse> {
    return new AgentsAPI(this.client).send("deepseek", ueo, question, options);
  }
}

export class QwenAPI {
  constructor(private client: AmdiClient) {}
  public async sendUeo(
    ueo: models.UniversalExportObject,
    question?: string,
    options?: { model?: string; temperature?: number; max_tokens?: number }
  ): Promise<models.ConnectorResponse> {
    return new AgentsAPI(this.client).send("qwen", ueo, question, options);
  }
}

export class LocalAPI {
  constructor(private client: AmdiClient) {}
  public async sendUeo(
    ueo: models.UniversalExportObject,
    question?: string,
    options?: { model?: string; temperature?: number; max_tokens?: number }
  ): Promise<models.ConnectorResponse> {
    return new AgentsAPI(this.client).send("local", ueo, question, options);
  }
}

export class VerificationAPI {
  constructor(private client: AmdiClient) {}

  public async verify(
    responseText: string,
    options?: {
      source_documents?: Record<string, any>;
      knowledge_base?: Record<string, any>;
    }
  ): Promise<models.VerificationReport> {
    const data = {
      response_text: responseText,
      ...options,
    };
    return this.client.request<models.VerificationReport>({
      method: "POST",
      url: "/api/v1/verify",
      data: data,
    });
  }
}

export class EnginesAPI {
  constructor(private client: AmdiClient) {}

  public async list(): Promise<string[]> {
    const response = await this.client.request({
      method: "GET",
      url: "/api/v1/engines",
    });
    return response.engines || [];
  }

  public async run(
    engine: string,
    documentId: string,
    params?: Record<string, any>
  ): Promise<models.EngineOutput> {
    const data = {
      document_id: documentId,
      ...params,
    };
    return this.client.request<models.EngineOutput>({
      method: "POST",
      url: `/api/v1/engines/${engine}/run`,
      data: data,
    });
  }
}

export class MemoryAPI {
  constructor(private client: AmdiClient) {}

  public async getStats(): Promise<Record<string, any>> {
    return this.client.request<Record<string, any>>({
      method: "GET",
      url: "/api/v1/memory/stats",
    });
  }

  public async promote(
    level: number,
    maxItems: number = 100
  ): Promise<Record<string, any>> {
    return this.client.request<Record<string, any>>({
      method: "POST",
      url: "/api/v1/memory/promote",
      data: { level, max_items: maxItems },
    });
  }

  public async evict(
    level: number,
    n: number = 10
  ): Promise<Record<string, any>> {
    return this.client.request<Record<string, any>>({
      method: "POST",
      url: "/api/v1/memory/evict",
      data: { level, n: n },
    });
  }

  public async maintenance(): Promise<Record<string, number>> {
    return this.client.request<Record<string, number>>({
      method: "POST",
      url: "/api/v1/memory/maintenance",
    });
  }
}

export class DashboardsAPI {
  constructor(private client: AmdiClient) {}

  public async get(dashboard: string): Promise<Record<string, any>> {
    return this.client.request<Record<string, any>>({
      method: "GET",
      url: `/api/v1/dashboards/${dashboard}`,
    });
  }

  public async uploadDashboard(): Promise<Record<string, any>> {
    return this.get("upload");
  }

  public async documentExplorer(): Promise<Record<string, any>> {
    return this.get("documents");
  }

  public async memoryDashboard(): Promise<Record<string, any>> {
    return this.get("memory");
  }

  public async analytics(): Promise<Record<string, any>> {
    return this.get("analytics");
  }

  public async performance(): Promise<Record<string, any>> {
    return this.get("performance");
  }
}
