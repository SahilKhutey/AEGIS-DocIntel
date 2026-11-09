import { DocumentSchema, type DocumentItem } from "@/lib/schemas";
import { apiRequest } from "@/lib/api-client";

export type UploadResult = {
  documentId: string;
  document: DocumentItem;
  processingJobId?: string;
};

export interface UploadService {
  upload(
    file: File,
    options?: {
      signal?: AbortSignal;
      onProgress?: (progress: number) => void;
    }
  ): Promise<UploadResult>;
}

export class DefaultUploadService implements UploadService {
  async upload(
    file: File,
    options?: {
      signal?: AbortSignal;
      onProgress?: (progress: number) => void;
    }
  ): Promise<UploadResult> {
    const formData = new FormData();
    formData.append("file", file);

    if (options?.onProgress) {
      options.onProgress(50);
    }

    const doc = await apiRequest("/api/v1/documents/upload", DocumentSchema, {
      method: "POST",
      body: formData,
      signal: options?.signal,
    });

    if (options?.onProgress) {
      options.onProgress(100);
    }

    return {
      documentId: doc.doc_id,
      document: doc,
    };
  }
}

export const defaultUploadService = new DefaultUploadService();
