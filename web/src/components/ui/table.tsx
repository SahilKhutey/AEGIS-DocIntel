import React from "react";
import { cn } from "@/lib/cn";

export interface TableProps extends React.HTMLAttributes<HTMLTableElement> {
  containerClassName?: string;
}

export function Table({
  className,
  containerClassName,
  children,
  ...props
}: TableProps) {
  return (
    <div
      className={cn(
        "w-full overflow-x-auto rounded-[var(--radius-md)] border border-[var(--border)]",
        containerClassName
      )}
    >
      <table
        className={cn(
          "w-full caption-bottom text-sm text-left border-collapse",
          className
        )}
        {...props}
      >
        {children}
      </table>
    </div>
  );
}

export function TableHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead
      className={cn(
        "bg-[var(--surface-muted)] border-b border-[var(--border)] text-xs font-semibold text-[var(--muted)] uppercase tracking-wider",
        className
      )}
      {...props}
    />
  );
}

export function TableBody({
  className,
  ...props
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <tbody
      className={cn(
        "divide-y divide-[var(--border)] bg-[var(--surface)] text-[var(--foreground)]",
        className
      )}
      {...props}
    />
  );
}

export function TableRow({
  className,
  ...props
}: React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr
      className={cn(
        "transition-colors hover:bg-[var(--surface-muted)]/50",
        className
      )}
      {...props}
    />
  );
}

export function TableHead({
  className,
  ...props
}: React.ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      scope="col"
      className={cn("px-4 py-3 font-semibold text-left align-middle", className)}
      {...props}
    />
  );
}

export function TableCell({
  className,
  ...props
}: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className={cn("px-4 py-3 align-middle", className)} {...props} />
  );
}

export function TableCaption({
  className,
  ...props
}: React.HTMLAttributes<HTMLTableCaptionElement>) {
  return (
    <caption
      className={cn("mt-4 text-xs text-[var(--muted)]", className)}
      {...props}
    />
  );
}
