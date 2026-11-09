import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type SkeletonVariant = "text" | "card" | "table" | "circular";

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: SkeletonVariant;
}

export function Skeleton({
  variant = "text",
  className,
  ...props
}: SkeletonProps) {
  return (
    <div
      aria-busy="true"
      aria-hidden="true"
      className={cn(
        "animate-pulse bg-[var(--surface-muted)]",
        variant === "text" && "h-4 w-full rounded-[var(--radius-sm)]",
        variant === "card" &&
          "h-32 w-full rounded-[var(--radius-lg)] border border-[var(--border)]",
        variant === "table" && "h-10 w-full rounded-[var(--radius-md)]",
        variant === "circular" && "h-10 w-10 rounded-full",
        className
      )}
      {...props}
    />
  );
}
