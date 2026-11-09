import type { SelectHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  invalid?: boolean;
};

export function Select({
  invalid = false,
  className,
  children,
  ...props
}: SelectProps) {
  return (
    <select
      aria-invalid={invalid || undefined}
      className={cn(
        "w-full min-h-10 rounded-[var(--radius-md)]",
        "border bg-[var(--surface)] px-3 py-2",
        "text-[var(--foreground)]",
        "border-[var(--border)]",
        "focus-visible:outline focus-visible:outline-2",
        "focus-visible:outline-[var(--primary)]",
        invalid &&
          "border-[var(--danger)] text-[var(--danger)] focus-visible:outline-[var(--danger)]",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    >
      {children}
    </select>
  );
}
