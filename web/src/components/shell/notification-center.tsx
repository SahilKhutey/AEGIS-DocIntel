"use client";

import { useState, useRef, useEffect } from "react";
import { Bell, Check, CheckCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Notification } from "@/features/notifications/types";

type NotificationCenterProps = {
  items?: Notification[];
  unreadCount?: number;
  onMarkRead?: (id: string) => Promise<void>;
  onMarkAllRead?: () => Promise<void>;
};

export function NotificationCenter({
  items = [],
  unreadCount = 0,
  onMarkRead,
  onMarkAllRead,
}: NotificationCenterProps) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
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

  async function markAll() {
    if (!onMarkAllRead || busy) return;

    setBusy(true);
    setError(null);

    try {
      await onMarkAllRead();
    } catch {
      setError("Unable to update notifications.");
    } finally {
      setBusy(false);
    }
  }

  async function markRead(id: string) {
    if (!onMarkRead || busy) return;

    setBusy(true);
    setError(null);

    try {
      await onMarkRead(id);
    } catch {
      setError("Unable to mark notification as read.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative" ref={containerRef}>
      <Button
        variant="ghost"
        size="sm"
        aria-label={`Notifications, ${unreadCount} unread`}
        aria-expanded={open}
        aria-controls="notification-panel"
        onClick={() => setOpen((value) => !value)}
        className="relative text-[var(--muted)] hover:text-[var(--foreground)]"
      >
        <Bell className="h-5 w-5" aria-hidden="true" />
        {unreadCount > 0 && (
          <span
            aria-hidden="true"
            className="absolute -top-1 -right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-[var(--danger)] px-1 text-[10px] font-bold text-white"
          >
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </Button>

      {open && (
        <section
          id="notification-panel"
          aria-label="Notifications"
          className="absolute right-0 top-full z-50 mt-2 w-[min(24rem,calc(100vw-2rem))] rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-md)]"
        >
          <header className="flex items-center justify-between border-b border-[var(--border)] p-3">
            <h2 className="text-sm font-semibold text-[var(--foreground)]">Notifications</h2>

            <Button
              variant="ghost"
              size="sm"
              disabled={busy || unreadCount === 0 || !onMarkAllRead}
              onClick={() => void markAll()}
              className="text-xs h-7 px-2"
            >
              <CheckCheck className="mr-1 h-3.5 w-3.5" aria-hidden="true" />
              Mark all read
            </Button>
          </header>

          {error && (
            <p role="alert" className="p-3 text-xs text-[var(--danger)] bg-red-50">
              {error}
            </p>
          )}

          <ul className="max-h-80 divide-y divide-[var(--border)] overflow-y-auto">
            {items.length === 0 ? (
              <li className="p-6 text-center text-xs text-[var(--muted)]">
                No notifications
              </li>
            ) : (
              items.map((item) => (
                <li key={item.id} className="p-3 hover:bg-[var(--surface-muted)]/50 transition-colors">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold text-[var(--foreground)] truncate">
                        {item.title}
                      </p>
                      <p className="mt-0.5 text-xs text-[var(--muted)] line-clamp-2">
                        {item.message}
                      </p>
                      <time
                        className="mt-1 block text-[10px] text-[var(--muted)]"
                        dateTime={item.createdAt}
                      >
                        {new Date(item.createdAt).toLocaleString()}
                      </time>
                    </div>

                    {!item.readAt && onMarkRead && (
                      <Button
                        variant="ghost"
                        size="sm"
                        aria-label={`Mark ${item.title} as read`}
                        disabled={busy}
                        onClick={() => void markRead(item.id)}
                        className="h-6 w-6 p-0 text-[var(--muted)] hover:text-[var(--foreground)] shrink-0"
                      >
                        <Check className="h-3.5 w-3.5" aria-hidden="true" />
                      </Button>
                    )}
                  </div>
                </li>
              ))
            )}
          </ul>
        </section>
      )}
    </div>
  );
}
