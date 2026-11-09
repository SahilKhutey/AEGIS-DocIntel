import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type AlertVariant = "info" | "success" | "warning" | "danger";

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant;
  title?: string;
}

const alertStyles: Record<
  AlertVariant,
  { container: string; icon: string; defaultTitle: string }
> = {
  info: {
    container: "bg-sky-50 border-sky-200 text-sky-900",
    icon: "ℹ️",
    defaultTitle: "Note",
  },
  success: {
    container: "bg-emerald-50 border-emerald-200 text-emerald-900",
    icon: "✓",
    defaultTitle: "Success",
  },
  warning: {
    container: "bg-amber-50 border-amber-200 text-amber-900",
    icon: "⚠",
    defaultTitle: "Warning",
  },
  danger: {
    container: "bg-rose-50 border-rose-200 text-rose-900",
    icon: "⨂",
    defaultTitle: "Error",
  },
};

export function Alert({
  variant = "info",
  title,
  children,
  className,
  ...props
}: AlertProps) {
  const style = alertStyles[variant];
  const role =
    variant === "danger" || variant === "warning" ? "alert" : "status";

  return (
    <div
      role={role}
      className={cn(
        "rounded-[var(--radius-md)] border p-4 text-sm flex gap-3 items-start",
        style.container,
        className
      )}
      {...props}
    >
      <span
        className="font-bold text-base leading-none select-none"
        aria-hidden="true"
      >
        {style.icon}
      </span>
      <div className="flex-1">
        {title && <h5 className="font-semibold mb-1 leading-snug">{title}</h5>}
        <div className="leading-relaxed">{children}</div>
      </div>
    </div>
  );
}
