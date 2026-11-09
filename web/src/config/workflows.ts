export type WorkflowStep = {
  id: string;
  label: string;
  action: string;
  expectedOutcome: string;
};

export type WorkflowDefinition = {
  id: string;
  title: string;
  entryRoute: string;
  requiredPermissions: string[];
  steps: WorkflowStep[];
  failureStates: string[];
};

export const WORKFLOWS: WorkflowDefinition[] = [
  {
    id: "document-ingestion",
    title: "Document Ingestion",
    entryRoute: "/documents",
    requiredPermissions: ["documents.upload"],
    steps: [
      {
        id: "select",
        label: "Select document",
        action: "Choose a local document",
        expectedOutcome: "File selected",
      },
      {
        id: "validate",
        label: "Validate document",
        action: "Check file constraints",
        expectedOutcome: "Valid file or validation error",
      },
      {
        id: "upload",
        label: "Upload document",
        action: "Submit to document API",
        expectedOutcome: "Server-confirmed upload result",
      },
      {
        id: "process",
        label: "Track processing",
        action: "Read document processing state",
        expectedOutcome: "Current processing state",
      },
      {
        id: "inspect",
        label: "Inspect result",
        action: "Open document details",
        expectedOutcome: "Authorized document details",
      },
    ],
    failureStates: [
      "invalid_file",
      "upload_failed",
      "processing_failed",
      "unauthorized",
      "network_error",
    ],
  },
  {
    id: "intelligence-query",
    title: "Intelligence Query",
    entryRoute: "/ask",
    requiredPermissions: ["intelligence.query"],
    steps: [
      {
        id: "scope",
        label: "Choose source scope",
        action: "Select authorized documents",
        expectedOutcome: "Valid source scope",
      },
      {
        id: "query",
        label: "Submit question",
        action: "Send query to intelligence API",
        expectedOutcome: "Server response",
      },
      {
        id: "evidence",
        label: "Inspect evidence",
        action: "Open source citations",
        expectedOutcome: "Traceable evidence",
      },
    ],
    failureStates: [
      "empty_query",
      "insufficient_evidence",
      "conflicting_evidence",
      "unauthorized",
      "network_error",
    ],
  },
  {
    id: "document-comparison",
    title: "Document Comparison",
    entryRoute: "/compare",
    requiredPermissions: ["documents.compare"],
    steps: [
      {
        id: "select-a",
        label: "Select first document",
        action: "Choose authorized source A",
        expectedOutcome: "Source A selected",
      },
      {
        id: "select-b",
        label: "Select second document",
        action: "Choose authorized source B",
        expectedOutcome: "Source B selected",
      },
      {
        id: "compare",
        label: "Run comparison",
        action: "Submit comparison request",
        expectedOutcome: "Comparison response",
      },
      {
        id: "inspect",
        label: "Inspect findings",
        action: "Review differences and evidence",
        expectedOutcome: "Traceable comparison findings",
      },
    ],
    failureStates: [
      "same_document",
      "missing_document",
      "unauthorized",
      "comparison_failed",
      "network_error",
    ],
  },
  {
    id: "governance-review",
    title: "Governance Review",
    entryRoute: "/reviews",
    requiredPermissions: ["governance.review"],
    steps: [
      {
        id: "queue",
        label: "Open review queue",
        action: "Load authorized review items",
        expectedOutcome: "Review queue displayed",
      },
      {
        id: "inspect",
        label: "Inspect candidate",
        action: "Read candidate and evidence",
        expectedOutcome: "Review context displayed",
      },
      {
        id: "decide",
        label: "Submit decision",
        action: "Send allowed decision to backend",
        expectedOutcome: "Server-confirmed decision",
      },
      {
        id: "audit",
        label: "Verify outcome",
        action: "Refresh review and audit state",
        expectedOutcome: "Updated authoritative state",
      },
    ],
    failureStates: [
      "stale_review",
      "decision_not_allowed",
      "evidence_missing",
      "unauthorized",
      "submission_failed",
    ],
  },
];
