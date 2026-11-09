import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  invalid?: boolean;
};

export function Input({
  invalid = false,
  className,
  ...props
}: InputProps) {
  return (
    <input
      aria-invalid={invalid || undefined}
      className={cn(
        "w-full min-h-10 rounded-[var(--radius-md)]",
        "border bg-[var(--surface)] px-3 py-2",
        "text-[var(--foreground)] placeholder:text-[var(--muted)]",
        "border-[var(--border)]",
        "focus-visible:outline focus-visible:outline-2",
        "focus-visible:outline-[var(--primary)]",
        invalid &&
          "border-[var(--danger)] text-[var(--danger)] focus-visible:outline-[var(--danger)]",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}
