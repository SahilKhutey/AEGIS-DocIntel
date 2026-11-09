import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type CardVariant = "default" | "interactive" | "selected";

export type CardProps = HTMLAttributes<HTMLDivElement> & {
  variant?: CardVariant;
};

export function Card({
  variant = "default",
  className,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        "rounded-[var(--radius-lg)]",
        "border border-[var(--border)]",
        "bg-[var(--surface)] p-5 shadow-[var(--shadow-sm)]",
        variant === "interactive" &&
          "transition-shadow hover:shadow-[var(--shadow-md)] cursor-pointer",
        variant === "selected" &&
          "border-[var(--primary)] ring-2 ring-[var(--primary)]/20",
        className
      )}
      {...props}
    />
  );
}
