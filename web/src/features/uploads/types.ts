export type UploadState =
  | "queued"
  | "validating"
  | "uploading"
  | "registering"
  | "uploaded"
  | "failed"
  | "cancelled";

export type UploadItem = {
  id: string;
  file: File;
  state: UploadState;
  progress: number;
  error?: string;
  documentId?: string;
};

export type UploadPolicy = {
  allowedMimeTypes: string[];
  maxFileSizeBytes: number;
  maxFilesPerRequest: number;
};

export const DEFAULT_UPLOAD_POLICY: UploadPolicy = {
  allowedMimeTypes: [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/html",
    "text/plain",
  ],
  maxFileSizeBytes: 200 * 1024 * 1024, // 200 MB
  maxFilesPerRequest: 10,
};
