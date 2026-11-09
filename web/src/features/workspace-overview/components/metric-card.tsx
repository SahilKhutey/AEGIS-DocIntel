import React from "react";
import Link from "next/link";
import { cn } from "@/lib/cn";

export type MetricCardProps = {
  label: string;
  value: number | string;
  icon?: React.ReactNode;
  subtext?: string;
  href?: string;
  variant?: "default" | "success" | "warning" | "danger" | "info";
};

const variantStyles: Record<
  NonNullable<MetricCardProps["variant"]>,
  { border: string; valueColor: string; bg: string }
> = {
  default: {
    border: "border-[var(--border)]",
    valueColor: "text-[var(--foreground)]",
    bg: "bg-[var(--surface)]",
  },
  success: {
    border: "border-emerald-200 dark:border-emerald-900/50",
    valueColor: "text-emerald-700 dark:text-emerald-400",
    bg: "bg-emerald-50/40 dark:bg-emerald-950/20",
  },
  warning: {
    border: "border-amber-200 dark:border-amber-900/50",
    valueColor: "text-amber-700 dark:text-amber-400",
    bg: "bg-amber-50/40 dark:bg-amber-950/20",
  },
  danger: {
    border: "border-red-200 dark:border-red-900/50",
    valueColor: "text-red-700 dark:text-red-400",
    bg: "bg-red-50/40 dark:bg-red-950/20",
  },
  info: {
    border: "border-blue-200 dark:border-blue-900/50",
    valueColor: "text-blue-700 dark:text-blue-400",
    bg: "bg-blue-50/40 dark:bg-blue-950/20",
  },
};

export function MetricCard({
  label,
  value,
  icon,
  subtext,
  href,
  variant = "default",
}: MetricCardProps) {
  const styles = variantStyles[variant];

  const content = (
    <div
      className={cn(
        "rounded-xl border p-5 shadow-2xs transition-all",
        styles.border,
        styles.bg,
        href && "hover:shadow-xs hover:border-[var(--primary)]"
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
          {label}
        </span>
        {icon && <div className="text-[var(--muted)]">{icon}</div>}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span
          className={cn(
            "text-3xl font-bold tracking-tight tabular-nums",
            styles.valueColor
          )}
        >
          {typeof value === "number" ? value.toLocaleString() : value}
        </span>
      </div>

      {subtext && (
        <p className="mt-1 text-xs text-[var(--muted)]">{subtext}</p>
      )}
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="block group">
        {content}
      </Link>
    );
  }

  return content;
}
