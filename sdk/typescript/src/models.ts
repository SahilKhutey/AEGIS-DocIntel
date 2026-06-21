export interface DocumentSummary {
  document_id: string;
  name: string;
  file_type: string;
  size_bytes: number;
  page_count: number;
  uploaded_at?: string;
  processed: boolean;
  tags: string[];
  metadata: Record<string, any>;
}

export interface Document {
  document_id: string;
  name: string;
  file_type: string;
  size_bytes: number;
  page_count: number;
  text: string;
  metadata: Record<string, any>;
  engine_reports: Record<string, any>;
}

export interface RetrievalHit {
  doc_id: string;
  fused_score: number;
  methods_found: string[];
  per_method_score: Record<string, number>;
  snippet: string;
}

export interface RetrievalResult {
  query: string;
  hits: RetrievalHit[];
  per_method_counts: Record<string, number>;
  latency_ms: number;
  total_candidates: number;
}

export interface Citation {
  doc_id: string;
  page?: number;
  section: string;
  excerpt: string;
}

export interface UniversalExportObject {
  system: string;
  context: string;
  summary: string;
  citations: Citation[];
  metadata: Record<string, any>;
  confidence: number;
  total_tokens: number;
  agent_specific: Record<string, any>;
  version: string;
}

export interface ConnectorResponse {
  text: string;
  agent: string;
  model: string;
  usage: Record<string, number>;
  finish_reason: string;
  latency_ms: number;
  metadata: Record<string, any>;
  success: boolean;
  error?: string;
}

export interface EngineOutput {
  engine_name: string;
  data: Record<string, any>;
  confidence: number;
  latency_ms: number;
}

export interface VerificationReport {
  passed: boolean;
  confidence: number;
  grade: string;
  citation_accuracy: number;
  fact_accuracy: number;
  hallucination_rate: number;
  issues: string[];
  recommendation: string;
}
