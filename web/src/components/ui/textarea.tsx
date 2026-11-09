import type { TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  invalid?: boolean;
};

export function Textarea({
  invalid = false,
  className,
  ...props
}: TextareaProps) {
  return (
    <textarea
      aria-invalid={invalid || undefined}
      className={cn(
        "w-full min-h-24 rounded-[var(--radius-md)]",
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
