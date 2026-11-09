"use client";

import { useState, useRef, useEffect } from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Workspace } from "@/features/workspaces/types";

type WorkspaceSelectorProps = {
  workspaces?: Workspace[];
  activeWorkspaceId?: string;
  onSelect?: (workspaceId: string) => Promise<void>;
};

export function WorkspaceSelector({
  workspaces = [
    { id: "workspace-default", name: "Primary Workspace", description: "Default workspace" },
  ],
  activeWorkspaceId = "workspace-default",
  onSelect,
}: WorkspaceSelectorProps) {
  const [open, setOpen] = useState(false);
  const [changing, setChanging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const activeWorkspace = workspaces.find(
    (workspace) => workspace.id === activeWorkspaceId
  ) || workspaces[0];

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

  async function handleSelect(id: string) {
    if (id === activeWorkspaceId || changing) {
      setOpen(false);
      return;
    }

    if (!onSelect) {
      setOpen(false);
      return;
    }

    setChanging(true);
    setError(null);

    try {
      await onSelect(id);
      setOpen(false);
    } catch {
      setError("Unable to switch workspace. Please retry.");
    } finally {
      setChanging(false);
    }
  }

  return (
    <div className="relative" ref={containerRef}>
      <Button
        variant="outline"
        size="sm"
        disabled={changing}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={activeWorkspace?.name ? `${activeWorkspace.name} — Select workspace` : "Select workspace"}
        onClick={() => setOpen((value) => !value)}
        className="flex items-center gap-2 border-[var(--border)] bg-[var(--surface)] font-medium text-xs sm:text-sm"
      >
        <span className="max-w-36 sm:max-w-44 truncate">
          {activeWorkspace?.name ?? "Select workspace"}
        </span>
        <ChevronsUpDown className="h-4 w-4 text-[var(--muted)]" aria-hidden="true" />
      </Button>

      {open && (
        <div
          role="listbox"
          aria-label="Available workspaces"
          className="absolute left-0 top-full z-50 mt-2 w-64 rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] p-1 shadow-[var(--shadow-md)]"
        >
          {workspaces.map((workspace) => (
            <button
              key={workspace.id}
              type="button"
              role="option"
              aria-selected={workspace.id === activeWorkspaceId}
              disabled={changing}
              onClick={() => void handleSelect(workspace.id)}
              className="flex min-h-10 w-full items-center justify-between rounded-[var(--radius-md)] px-3 text-left text-sm hover:bg-[var(--surface-muted)] transition-colors cursor-pointer disabled:opacity-50"
            >
              <div className="truncate">
                <span className="block font-medium text-[var(--foreground)] truncate">
                  {workspace.name}
                </span>
                {workspace.description && (
                  <span className="block text-xs text-[var(--muted)] truncate">
                    {workspace.description}
                  </span>
                )}
              </div>
              {workspace.id === activeWorkspaceId && (
                <Check className="h-4 w-4 text-[var(--primary)] shrink-0 ml-2" aria-hidden="true" />
              )}
            </button>
          ))}
        </div>
      )}

      {error && (
        <p role="alert" className="absolute left-0 top-full mt-1 text-xs text-[var(--danger)]">
          {error}
        </p>
      )}
    </div>
  );
}
