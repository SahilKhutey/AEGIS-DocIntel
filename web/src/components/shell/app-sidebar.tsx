"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Files,
  Workflow,
  MessageSquare,
  GitCompare,
  FileSearch,
  ClipboardCheck,
  ChartNoAxesCombined,
  Plug,
  Settings,
  ShieldCheck,
} from "lucide-react";

import { getVisibleNavigation } from "./navigation-access";
import { cn } from "@/lib/cn";

const iconMap = {
  "layout-dashboard": LayoutDashboard,
  files: Files,
  workflow: Workflow,
  "message-square": MessageSquare,
  "git-compare": GitCompare,
  "file-search": FileSearch,
  "clipboard-check": ClipboardCheck,
  "chart-no-axes-combined": ChartNoAxesCombined,
  plug: Plug,
  settings: Settings,
};

type AppSidebarProps = {
  permissions: readonly string[];
  collapsed?: boolean;
  onNavigate?: () => void;
};

export function AppSidebar({
  permissions,
  collapsed = false,
  onNavigate,
}: AppSidebarProps) {
  const pathname = usePathname() || "/";
  const groups = getVisibleNavigation(permissions);

  function isActive(href: string) {
    if (href === "/") return pathname === "/";
    return pathname === href || pathname.startsWith(`${href}/`);
  }

  return (
    <aside
      className={cn(
        "flex h-full flex-col border-r transition-all duration-200",
        "border-[var(--border)] bg-[var(--surface)]",
        collapsed ? "w-[4.5rem]" : "w-64"
      )}
    >
      <div className="flex h-16 items-center gap-3 px-4 border-b border-[var(--border)]">
        <Link
          href="/"
          aria-label="AEGIS home"
          className="flex items-center gap-3"
          onClick={onNavigate}
        >
          <ShieldCheck
            className="h-7 w-7 shrink-0 text-[var(--primary)]"
            aria-hidden="true"
          />
          {!collapsed && (
            <span className="text-lg font-bold tracking-tight text-[var(--foreground)]">
              AEGIS
              <span className="ml-1 text-xs font-semibold text-[var(--primary)]">
                DocIntel
              </span>
            </span>
          )}
        </Link>
      </div>

      <nav
        aria-label="Primary navigation"
        className="flex-1 space-y-6 overflow-y-auto px-3 py-4"
      >
        {groups.map((group) => (
          <section key={group.id} aria-label={group.label}>
            {!collapsed && (
              <h2 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
                {group.label}
              </h2>
            )}

            <ul className="space-y-1">
              {group.items.map((item) => {
                const Icon = iconMap[item.icon as keyof typeof iconMap] || Files;
                const active = isActive(item.href);

                return (
                  <li key={item.id}>
                    <Link
                      href={item.href}
                      onClick={onNavigate}
                      aria-current={active ? "page" : undefined}
                      title={collapsed ? item.label : undefined}
                      className={cn(
                        "flex min-h-10 items-center gap-3 rounded-md px-3",
                        "text-sm font-medium transition-colors",
                        active
                          ? "bg-blue-50 text-blue-800 font-semibold"
                          : "text-[var(--foreground)] hover:bg-[var(--surface-muted)]"
                      )}
                    >
                      <Icon
                        className={cn(
                          "h-4 w-4 shrink-0",
                          active ? "text-[var(--primary)]" : "text-[var(--muted)]"
                        )}
                        aria-hidden="true"
                      />
                      {!collapsed && <span>{item.label}</span>}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </section>
        ))}
      </nav>
    </aside>
  );
}
