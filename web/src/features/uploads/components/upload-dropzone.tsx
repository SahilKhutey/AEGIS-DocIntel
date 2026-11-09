"use client";

import { useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";

type UploadDropzoneProps = {
  accept?: string;
  multiple?: boolean;
  disabled?: boolean;
  onFilesSelected: (files: File[]) => void;
};

export function UploadDropzone({
  accept = ".pdf,.docx,.pptx,.html,.txt,application/pdf,text/plain,text/html",
  multiple = true,
  disabled = false,
  onFilesSelected,
}: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function selectFiles(files: FileList | null) {
    if (!files || disabled) return;
    onFilesSelected(Array.from(files));
  }

  return (
    <section
      aria-label="Upload document dropzone"
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        selectFiles(event.dataTransfer.files);
      }}
      className={[
        "rounded-xl border-2 border-dashed p-8 text-center transition-colors cursor-pointer",
        dragging
          ? "border-[var(--primary)] bg-[var(--surface-muted)]"
          : "border-[var(--border)] hover:border-[var(--primary)] hover:bg-[var(--surface-muted)]",
        disabled ? "opacity-50 cursor-not-allowed" : "",
      ].join(" ")}
      onClick={() => inputRef.current?.click()}
    >
      <UploadCloud
        className="mx-auto h-10 w-10 text-[var(--muted)]"
        aria-hidden="true"
      />

      <p className="mt-3 font-medium text-[var(--foreground)]">
        Drag and drop files here
      </p>

      <p className="mt-1 text-sm text-[var(--muted)]">
        Or select files from your computer. (Max 200 MB per file)
      </p>

      <input
        ref={inputRef}
        type="file"
        className="sr-only"
        accept={accept}
        multiple={multiple}
        disabled={disabled}
        onChange={(event) => {
          selectFiles(event.target.files);
          event.currentTarget.value = "";
        }}
      />

      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={disabled}
        onClick={(e) => {
          e.stopPropagation();
          inputRef.current?.click();
        }}
        className="mt-4"
      >
        Browse files
      </Button>
    </section>
  );
}
