import type { UploadPolicy } from "./types";

export type ValidationResult = {
  valid: boolean;
  reason?: string;
  errors: string[];
};

export function validateUploadFile(
  file: File,
  policy: UploadPolicy
): ValidationResult {
  if (file.size <= 0) {
    const reason = "File cannot be empty (0 bytes).";
    return {
      valid: false,
      reason,
      errors: [reason],
    };
  }

  if (file.size > policy.maxFileSizeBytes) {
    const reason = "The file exceeds the maximum allowed size.";
    return {
      valid: false,
      reason,
      errors: [reason],
    };
  }

  if (file.type && !policy.allowedMimeTypes.includes(file.type)) {
    const reason = `File type "${file.type}" is not supported.`;
    return {
      valid: false,
      reason,
      errors: [reason],
    };
  }

  return { valid: true, errors: [] };
}
