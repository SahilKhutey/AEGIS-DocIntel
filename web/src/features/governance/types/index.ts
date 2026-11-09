/**
 * Domain types for WP-UI-06 Governance Workspace.
 * Aligned with backend contracts in src/engines/governance/contracts.py
 */

export type ReviewStatus =
  | "pending"
  | "in_review"
  | "approved"
  | "corrected"
  | "rejected"
  | "needs_evidence";

export type ReviewPriority = "high" | "medium" | "low";

export type CandidateType = "fact" | "conflict";

export type ReviewAction =
  | "create"
  | "claim"
  | "approve"
  | "correct"
  | "reject"
  | "request_evidence"
  | "reopen";

export type DecisionType = "approve" | "correct" | "reject" | "request_evidence";

export interface EvidenceReference {
  evidence_id?: string;
  document_id: string;
  chunk_id?: string;
  page_number?: number;
  quote: string;
  confidence?: number;
  section_path?: string[];
}

export type FactVerificationStatus =
  | "verified"
  | "partially_verified"
  | "not_verified"
  | "contradicted"
  | "insufficient_evidence";

export interface ExtractedFactData {
  fact_id?: string;
  subject?: string;
  attribute?: string;
  value?: unknown;
  raw_value?: string;
  confidence?: number;
  evidence_quote?: string;
  evidence_id?: string;
  document_id?: string;
  page_number?: number;
  temporal_anchor?: string;
  [key: string]: unknown;
}

export type ConflictResolutionOutcome =
  | "accepted_first_fact"
  | "accepted_second_fact"
  | "both_valid"
  | "insufficient_evidence"
  | "escalated";

export interface ConflictingFactClaim {
  fact_id?: string;
  document_id: string;
  value: unknown;
  raw_value?: string;
  confidence?: number;
  evidence_quote?: string;
  page_number?: number;
  published_date?: string;
}

export interface ConflictData {
  conflict_id?: string;
  subject: string;
  attribute: string;
  fact_1: ConflictingFactClaim;
  fact_2: ConflictingFactClaim;
  contradiction_type?: string;
  conflicting_document_ids?: string[];
  severity?: "critical" | "high" | "medium" | "low";
  [key: string]: unknown;
}

export interface ReviewRevision {
  revision_id: string;
  review_id: string;
  tenant_id: string;
  actor_id: string;
  version: number;
  corrected_value: unknown;
  corrected_type: string;
  unit?: string | null;
  evidence_quote?: string | null;
  rationale: string;
  created_at: string;
}

export interface ReviewItem {
  review_id: string;
  tenant_id: string;
  candidate_id: string;
  candidate_type: CandidateType;
  document_id: string;
  status: ReviewStatus;
  version: number;
  assigned_to?: string | null;
  candidate_data: Record<string, unknown>;
  current_revision_id?: string | null;
  current_revision?: ReviewRevision | null;
  created_at: string;
  updated_at: string;
  // Optional client-enriched fields
  priority?: ReviewPriority;
  field_name?: string;
  extracted_value?: string;
  page_number?: number;
  confidence?: number;
}

export interface DecisionSubmission {
  action: DecisionType;
  expected_version: number;
  rationale: string;
  corrected_value?: string | number | boolean;
  corrected_type?: string;
  unit?: string;
  evidence_quote?: string;
}

export interface AuditEvent {
  event_id: string;
  review_id: string;
  sequence: number;
  tenant_id: string;
  actor_id: string;
  action: string;
  previous_status: string;
  new_status: string;
  previous_version: number;
  new_version: number;
  rationale: string;
  revision_id?: string | null;
  request_id?: string | null;
  timestamp: string;
}

export interface GovernanceMetrics {
  total_items: number;
  decided_count: number;
  approval_rate: number;
  correction_rate: number;
  rejection_rate: number;
  evidence_failure_rate: number;
  feedback_categories?: Record<string, number>;
}

export interface ReviewQueueFiltersState {
  status: string;
  candidateType: "all" | "fact" | "conflict";
  assignment: "all" | "unassigned" | "assigned";
  searchQuery: string;
  sortBy: "updated_at" | "created_at" | "version" | "priority";
  sortOrder: "asc" | "desc";
}
