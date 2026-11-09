export type CitationReference = {
  citationId: string;
  documentId: string;
  documentName: string;
  pageNumber?: number;
  section?: string;
  passageId?: string;
  quote?: string;
  sourceUrl?: string;
};

export type AnswerClaim = {
  claimId: string;
  text: string;
  citationIds: string[];
  supportStatus:
    | "supported"
    | "partially_supported"
    | "unsupported"
    | "contradicted"
    | "unknown";
};

export type AskRequest = {
  question: string;
  documentIds?: string[];
  conversationId?: string;
};

export type AskResponse = {
  answer: string;
  conversationId?: string;
  claims?: AnswerClaim[];
  citations: CitationReference[];
  retrievalId?: string;
  warnings?: string[];
};

export type RetrievalRequest = {
  query: string;
  documentIds?: string[];
  page?: number;
  pageSize?: number;
};

export type RetrievalResult = {
  resultId: string;
  documentId: string;
  documentName: string;
  passageId: string;
  pageNumber?: number;
  section?: string;
  text: string;
  score?: number;
  rank?: number;
};

export type RetrievalResponse = {
  results: RetrievalResult[];
  total?: number;
  page?: number;
  pageSize?: number;
  retrievalId?: string;
};

export type EvidenceRecord = {
  evidenceId: string;
  documentId: string;
  documentName: string;
  passageId?: string;
  pageNumber?: number;
  section?: string;
  content: string;
  evidenceType?: string;
  relatedCitationIds?: string[];
};

export type KnowledgeNode = {
  id: string;
  label: string;
  type: string;
  documentIds?: string[];
};

export type KnowledgeEdge = {
  id: string;
  source: string;
  target: string;
  relationship: string;
};

export type KnowledgeGraphResponse = {
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
};

export type ComparisonRequest = {
  documentIds: string[];
  comparisonMode: "content" | "semantic" | "structured";
};

export type ComparisonDifference = {
  differenceId: string;
  category: string;
  description: string;
  leftEvidence?: CitationReference;
  rightEvidence?: CitationReference;
  significance?: "low" | "medium" | "high" | "unknown";
};

export type ComparisonResponse = {
  comparisonId: string;
  documentIds: string[];
  differences: ComparisonDifference[];
  summary?: string;
};
