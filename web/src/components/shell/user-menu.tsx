"use client";

import { useState, useRef, useEffect } from "react";
import { CircleUserRound, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";

type UserMenuProps = {
  displayName?: string;
  email?: string;
  onSignOut?: () => Promise<void>;
};

export function UserMenu({
  displayName = "Account",
  email,
  onSignOut,
}: UserMenuProps) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  async function handleSignOut() {
    if (!onSignOut || busy) return;

    setBusy(true);

    try {
      await onSignOut();
      setOpen(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative" ref={containerRef}>
      <Button
        variant="ghost"
        size="sm"
        aria-label="Open account menu"
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((value) => !value)}
        className="text-[var(--muted)] hover:text-[var(--foreground)]"
      >
        <CircleUserRound className="h-5 w-5" aria-hidden="true" />
      </Button>

      {open && (
        <div
          role="menu"
          aria-label="Account options"
          className="absolute right-0 top-full z-50 mt-2 w-56 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-2 shadow-[var(--shadow-md)]"
        >
          <div className="border-b border-[var(--border)] pb-2 mb-2 px-2 pt-1">
            <p className="text-xs font-semibold text-[var(--foreground)] truncate">
              {displayName}
            </p>
            {email && (
              <p className="truncate text-[11px] text-[var(--muted)] mt-0.5">
                {email}
              </p>
            )}
          </div>

          <Button
            variant="ghost"
            size="sm"
            disabled={busy}
            onClick={() => void handleSignOut()}
            className="w-full justify-start text-xs text-[var(--danger)] hover:bg-red-50 hover:text-[var(--danger)] cursor-pointer"
          >
            <LogOut className="mr-2 h-4 w-4" aria-hidden="true" />
            Sign out
          </Button>
        </div>
      )}
    </div>
  );
}
