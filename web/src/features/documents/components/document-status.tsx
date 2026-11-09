import { Badge, type BadgeVariant } from "@/components/ui/badge";
import type { DocumentStatus } from "../types";

const STATUS_LABELS: Record<DocumentStatus, string> = {
  uploaded: "Uploaded",
  queued: "Queued",
  processing: "Processing",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};

const STATUS_VARIANTS: Record<DocumentStatus, BadgeVariant> = {
  uploaded: "default",
  queued: "warning",
  processing: "info",
  completed: "success",
  failed: "danger",
  cancelled: "default",
};

export function DocumentStatusBadge({
  status,
  className,
}: {
  status: DocumentStatus;
  className?: string;
}) {
  const label = STATUS_LABELS[status] || status;
  const variant = STATUS_VARIANTS[status] || "default";

  return (
    <Badge
      variant={variant}
      className={className}
      aria-label={`Document status: ${label}`}
    >
      {label}
    </Badge>
  );
}
