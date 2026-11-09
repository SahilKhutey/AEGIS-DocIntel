import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type BadgeVariant =
  | "default"
  | "success"
  | "warning"
  | "danger"
  | "info";

const styles: Record<BadgeVariant, string> = {
  default:
    "bg-[var(--surface-muted)] text-[var(--foreground)]",
  success:
    "bg-green-100 text-green-900",
  warning:
    "bg-amber-100 text-amber-950",
  danger:
    "bg-red-100 text-red-900",
  info:
    "bg-sky-100 text-sky-950",
};

export function Badge({
  variant = "default",
  className,
  children,
  ...props
}: HTMLAttributes<HTMLSpanElement> & {
  variant?: BadgeVariant;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1",
        "text-xs font-medium",
        styles[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
