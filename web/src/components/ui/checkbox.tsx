import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export type CheckboxProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "type"
> & {
  label?: string;
};

export function Checkbox({
  label,
  className,
  id,
  disabled,
  ...props
}: CheckboxProps) {
  const inputId =
    id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  const checkboxElement = (
    <input
      type="checkbox"
      id={inputId}
      disabled={disabled}
      className={cn(
        "h-4 w-4 rounded-[var(--radius-sm)]",
        "border-[var(--border)] text-[var(--primary)]",
        "focus-visible:outline focus-visible:outline-2",
        "focus-visible:outline-[var(--primary)]",
        "disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer",
        className
      )}
      {...props}
    />
  );

  if (!label) {
    return checkboxElement;
  }

  return (
    <label
      htmlFor={inputId}
      className={cn(
        "inline-flex items-center gap-2 text-sm text-[var(--foreground)]",
        disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer"
      )}
    >
      {checkboxElement}
      <span>{label}</span>
    </label>
  );
}
