"use client";

import React, { useEffect, useId } from "react";
import { cn } from "@/lib/cn";
import { Button } from "./button";

export type DialogVariant = "default" | "confirmation" | "destructive";

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: React.ReactNode;
  description?: React.ReactNode;
  children?: React.ReactNode;
  variant?: DialogVariant;
  className?: string;
}

export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  variant = "default",
  className,
}: DialogProps) {
  const titleId = useId();
  const descId = useId();

  useEffect(() => {
    if (!open) return;

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="presentation"
    >
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descId : undefined}
        className={cn(
          "relative z-10 w-full max-w-lg rounded-[var(--radius-lg)]",
          "border border-[var(--border)] bg-[var(--surface)] p-6 shadow-[var(--shadow-md)]",
          variant === "destructive" && "border-[var(--danger)]",
          className
        )}
      >
        <div className="flex items-start justify-between gap-4 pb-3">
          <h2
            id={titleId}
            className="text-lg font-semibold text-[var(--foreground)]"
          >
            {title}
          </h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            aria-label="Close dialog"
            className="h-8 w-8 p-0 text-[var(--muted)] hover:text-[var(--foreground)]"
          >
            ✕
          </Button>
        </div>

        {description && (
          <p id={descId} className="text-sm text-[var(--muted)] pb-4">
            {description}
          </p>
        )}

        <div className="mt-2 text-sm text-[var(--foreground)]">{children}</div>
      </div>
    </div>
  );
}
