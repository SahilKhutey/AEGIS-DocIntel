/**
 * Shared Deterministic Test Data for AEGIS-DocIntel E2E & Validation Suites
 */

export interface TestWorkspace {
  id: string;
  name: string;
  role: "admin" | "analyst" | "reviewer" | "auditor";
}

export const TEST_WORKSPACES: TestWorkspace[] = [
  { id: "ws-primary", name: "Primary Workspace", role: "admin" },
  { id: "ws-finance", name: "Finance & Compliance", role: "reviewer" },
  { id: "ws-legal", name: "Legal Operations", role: "analyst" },
];

export interface TestDocumentItem {
  id: string;
  title: string;
  filename: string;
  mimeType: string;
  fileSizeBytes: number;
  status: "completed" | "processing" | "queued" | "failed";
  pageCount: number;
  confidenceScore: number;
  extractedFactsCount: number;
}

export const SYNTHETIC_DOCUMENTS: TestDocumentItem[] = [
  {
    id: "doc-alpha-001",
    title: "Master Services Agreement — Quantum Advisory",
    filename: "MSA_Quantum_Advisory_2026.pdf",
    mimeType: "application/pdf",
    fileSizeBytes: 2450000,
    status: "completed",
    pageCount: 18,
    confidenceScore: 0.98,
    extractedFactsCount: 42,
  },
  {
    id: "doc-beta-002",
    title: "Data Processing Addendum — Global Cloud",
    filename: "DPA_GlobalCloud_Annex_IV.pdf",
    mimeType: "application/pdf",
    fileSizeBytes: 1280000,
    status: "completed",
    pageCount: 12,
    confidenceScore: 0.95,
    extractedFactsCount: 29,
  },
  {
    id: "doc-gamma-003",
    title: "SOC 2 Type II Security Assessment",
    filename: "SOC2_Type_II_Report_2025.pdf",
    mimeType: "application/pdf",
    fileSizeBytes: 5400000,
    status: "processing",
    pageCount: 45,
    confidenceScore: 0.92,
    extractedFactsCount: 15,
  },
];

export interface SyntheticReviewItem {
  id: string;
  documentId: string;
  documentTitle: string;
  factKey: string;
  claimText: string;
  confidence: number;
  status: "pending_review" | "verified" | "flagged_conflict" | "escalated";
  priority: "high" | "medium" | "low";
  evidenceSnippet: string;
  pageNumber: number;
}

export const SYNTHETIC_REVIEWS: SyntheticReviewItem[] = [
  {
    id: "rev-sec-401",
    documentId: "doc-alpha-001",
    documentTitle: "Master Services Agreement — Quantum Advisory",
    factKey: "termination_notice_period",
    claimText: "Termination for convenience requires 90 calendar days prior written notice.",
    confidence: 0.96,
    status: "pending_review",
    priority: "high",
    evidenceSnippet: "Either party may terminate this Agreement without cause upon giving ninety (90) calendar days prior written notice to the other party.",
    pageNumber: 14,
  },
  {
    id: "rev-conf-502",
    documentId: "doc-beta-002",
    documentTitle: "Data Processing Addendum — Global Cloud",
    factKey: "liability_limitation_cap",
    claimText: "Liability is capped at 2x annual aggregate fees paid.",
    confidence: 0.74,
    status: "flagged_conflict",
    priority: "high",
    evidenceSnippet: "The total aggregate liability shall not exceed two times (2x) the amounts paid hereunder in the preceding twelve months, except in cases of gross negligence.",
    pageNumber: 8,
  },
];

export const SYNTHETIC_ROUTES = [
  { path: "/", label: "Overview", requiresAuth: true },
  { path: "/documents", label: "Documents", requiresAuth: true },
  { path: "/ask", label: "Ask AEGIS", requiresAuth: true },
  { path: "/compare", label: "Compare", requiresAuth: true },
  { path: "/reviews", label: "Governance Reviews", requiresAuth: true },
  { path: "/analytics", label: "Analytics", requiresAuth: true },
  { path: "/mathematics", label: "Mathematics", requiresAuth: true },
  { path: "/pipelines", label: "Pipelines", requiresAuth: true },
  { path: "/pipelines/job-run-9021", label: "Pipeline Run Detail", requiresAuth: true },
  { path: "/monitoring", label: "Monitoring", requiresAuth: true },
  { path: "/developer", label: "Developer", requiresAuth: true },
];
