export type DocumentStatus =
  | "uploaded"
  | "queued"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled";

export type DocumentRecord = {
  id: string;
  name: string;
  mimeType: string;
  sizeBytes: number;
  status: DocumentStatus;
  createdAt: string;
  updatedAt: string;
  pageCount?: number;
  chunkCount?: number;
  processingJobId?: string;
};

export type DocumentListResponse = {
  items: DocumentRecord[];
  total: number;
  page?: number;
  pageSize?: number;
  nextCursor?: string;
};

export type DocumentListQuery = {
  query?: string;
  status?: DocumentStatus;
  mimeType?: string;
  sortBy?: "name" | "createdAt" | "sizeBytes";
  sortOrder?: "asc" | "desc";
  cursor?: string;
  limit?: number;
  page?: number;
};

export type DocumentMetadata = {
  title?: string;
  author?: string;
  subject?: string;
  language?: string;
  pageCount?: number;
  chunkCount?: number;
  createdAt?: string;
  modifiedAt?: string;
};

export type ExtractedTextPage = {
  pageNumber: number;
  text: string;
  chunkId?: string;
  sectionTitle?: string;
};

export type DocumentInspection = {
  document: DocumentRecord;
  metadata: DocumentMetadata;
  extractedPages?: ExtractedTextPage[];
  previewAvailable: boolean;
  processingSummary?: {
    status: DocumentStatus;
    completedStages: number;
    totalStages: number;
  };
};
