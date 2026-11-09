type UploadProgressProps = {
  fileName: string;
  progress: number;
  state: string;
};

export function UploadProgress({
  fileName,
  progress,
  state,
}: UploadProgressProps) {
  const safeProgress = Math.max(0, Math.min(100, Math.round(progress)));

  return (
    <div className="space-y-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3">
      <div className="flex justify-between gap-3 text-sm">
        <span className="truncate font-medium text-[var(--foreground)]">{fileName}</span>
        <span className="text-[var(--muted)] tabular-nums">{safeProgress}%</span>
      </div>

      <div
        role="progressbar"
        aria-label={`Upload progress for ${fileName}`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={safeProgress}
        className="h-2 overflow-hidden rounded-full bg-[var(--surface-muted)]"
      >
        <div
          className="h-full rounded-full bg-[var(--primary)] transition-all duration-200"
          style={{ width: `${safeProgress}%` }}
        />
      </div>

      <p className="text-xs text-[var(--muted)]">{state}</p>
    </div>
  );
}
