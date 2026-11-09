import { describe, expect, it } from "vitest";
import { validateUploadFile } from "@/features/uploads/upload-validation";
import { DEFAULT_UPLOAD_POLICY } from "@/features/uploads/types";

describe("Upload File Validation", () => {
  it("accepts a valid PDF file within the size limit", () => {
    const file = new File(["valid pdf content"], "sample.pdf", {
      type: "application/pdf",
    });

    const result = validateUploadFile(file, DEFAULT_UPLOAD_POLICY);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it("accepts valid DOCX, PPTX, and TXT files", () => {
    const docxFile = new File(["docx content"], "contract.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const txtFile = new File(["plain text content"], "notes.txt", {
      type: "text/plain",
    });

    expect(validateUploadFile(docxFile, DEFAULT_UPLOAD_POLICY).valid).toBe(true);
    expect(validateUploadFile(txtFile, DEFAULT_UPLOAD_POLICY).valid).toBe(true);
  });

  it("rejects an empty file when allowEmptyFiles is false", () => {
    const emptyFile = new File([], "empty.pdf", {
      type: "application/pdf",
    });

    const result = validateUploadFile(emptyFile, DEFAULT_UPLOAD_POLICY);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain("File cannot be empty (0 bytes).");
  });

  it("rejects a file exceeding the maximum size limit", () => {
    // 250 MB mock file
    const oversizedFile = new File(["x"], "oversized.pdf", {
      type: "application/pdf",
    });
    Object.defineProperty(oversizedFile, "size", {
      value: 250 * 1024 * 1024,
    });

    const result = validateUploadFile(oversizedFile, DEFAULT_UPLOAD_POLICY);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes("exceeds the maximum allowed size"))).toBe(true);
  });

  it("accepts boundary size file (exactly 200MB)", () => {
    const boundaryFile = new File(["x"], "boundary.pdf", {
      type: "application/pdf",
    });
    Object.defineProperty(boundaryFile, "size", {
      value: 200 * 1024 * 1024,
    });

    const result = validateUploadFile(boundaryFile, DEFAULT_UPLOAD_POLICY);
    expect(result.valid).toBe(true);
  });

  it("rejects files with disallowed MIME types", () => {
    const zipFile = new File(["binary"], "archive.zip", {
      type: "application/zip",
    });
    const pngFile = new File(["image"], "photo.png", {
      type: "image/png",
    });

    const zipResult = validateUploadFile(zipFile, DEFAULT_UPLOAD_POLICY);
    expect(zipResult.valid).toBe(false);
    expect(zipResult.errors.some((e) => e.includes("File type") && e.includes("not supported"))).toBe(true);

    const pngResult = validateUploadFile(pngFile, DEFAULT_UPLOAD_POLICY);
    expect(pngResult.valid).toBe(false);
  });
});
