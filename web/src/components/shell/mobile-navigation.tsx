"use client";

import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AppSidebar } from "./app-sidebar";

type MobileNavigationProps = {
  open: boolean;
  permissions: readonly string[];
  onClose: () => void;
};

export function MobileNavigation({
  open,
  permissions,
  onClose,
}: MobileNavigationProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, onClose]);

  useEffect(() => {
    if (!open) return;

    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previous;
    };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      <button
        type="button"
        aria-label="Close navigation overlay"
        className="absolute inset-0 bg-black/50 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      <section
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Mobile navigation"
        className="relative flex h-full w-[min(20rem,85vw)] flex-col bg-[var(--surface)] shadow-xl z-10"
      >
        <div className="flex h-16 items-center justify-between border-b border-[var(--border)] px-4">
          <span className="text-sm font-bold tracking-tight text-[var(--foreground)]">
            AEGIS <span className="text-xs text-[var(--primary)] font-semibold">DocIntel</span>
          </span>
          <Button
            variant="ghost"
            size="sm"
            aria-label="Close navigation"
            onClick={onClose}
            className="h-8 w-8 p-0 text-[var(--muted)] hover:text-[var(--foreground)]"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </Button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto">
          <AppSidebar
            permissions={permissions}
            onNavigate={onClose}
          />
        </div>
      </section>
    </div>
  );
}
