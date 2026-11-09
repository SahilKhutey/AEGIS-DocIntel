"use client";

import React, { useState, useCallback, useMemo, Suspense } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AppSidebar } from "./app-sidebar";
import { AppHeader } from "./app-header";
import { MobileNavigation } from "./mobile-navigation";
import { Breadcrumbs } from "./breadcrumbs";
import { ShellSkeleton } from "./shell-skeleton";
import { getVisibleNavigation } from "./navigation-access";
import type { Workspace } from "@/features/workspaces/types";
import type { Notification } from "@/features/notifications/types";
import type { GlobalSearchResponse } from "@/features/search/types";

export type AppShellProps = {
  children: React.ReactNode;
  permissions?: readonly string[];
  workspaces?: Workspace[];
  activeWorkspaceId?: string;
  onWorkspaceSelect?: (id: string) => Promise<void>;
  notifications?: Notification[];
  unreadNotificationCount?: number;
  onMarkNotificationRead?: (id: string) => Promise<void>;
  onMarkAllNotificationsRead?: () => Promise<void>;
  onSearch?: (query: string) => Promise<GlobalSearchResponse>;
  userDisplayName?: string;
  userEmail?: string;
  onSignOut?: () => Promise<void>;
  collapsed?: boolean;
};

const DEFAULT_WORKSPACES: Workspace[] = [
  {
    id: "workspace-default",
    name: "Primary Workspace",
    description: "Default analytical workspace",
  },
];

const DEFAULT_PERMISSIONS = [
  "workspace.read",
  "documents.read",
  "documents.upload",
  "documents.compare",
  "processing.read",
  "intelligence.query",
  "governance.read",
  "evidence.read",
];

function AppShellInner({
  children,
  permissions: explicitPermissions,
  workspaces = DEFAULT_WORKSPACES,
  activeWorkspaceId: initialWorkspaceId = "workspace-default",
  onWorkspaceSelect,
  notifications = [],
  unreadNotificationCount = 0,
  onMarkNotificationRead,
  onMarkAllNotificationsRead,
  onSearch,
  userDisplayName = "Analyst",
  userEmail = "analyst@aegis.internal",
  onSignOut,
  collapsed = false,
}: AppShellProps) {
  const pathname = usePathname() || "/";

  const permissions = useMemo(() => {
    if (explicitPermissions) return explicitPermissions;
    return DEFAULT_PERMISSIONS;
  }, [explicitPermissions]);

  const [mobileOpen, setMobileOpen] = useState(false);
  const [currentWorkspaceId, setCurrentWorkspaceId] = useState(initialWorkspaceId);

  const closeMobile = useCallback(() => {
    setMobileOpen(false);
  }, []);

  const handleWorkspaceSelect = useCallback(
    async (id: string) => {
      if (onWorkspaceSelect) {
        await onWorkspaceSelect(id);
      }
      setCurrentWorkspaceId(id);
    },
    [onWorkspaceSelect]
  );

  const mobileNavItems = useMemo(() => {
    return getVisibleNavigation(permissions).flatMap((g) => g.items);
  }, [permissions]);

  return (
    <>
      <div className="flex min-h-screen flex-1">
        {/* Desktop Sidebar */}
        <div className="hidden shrink-0 lg:block">
          <AppSidebar
            permissions={permissions}
            collapsed={collapsed}
          />
        </div>

        {/* Main Content Area */}
        <div className="flex min-w-0 flex-1 flex-col">
          <AppHeader
            workspaces={workspaces}
            activeWorkspaceId={currentWorkspaceId}
            onWorkspaceSelect={handleWorkspaceSelect}
            onMenuClick={() => setMobileOpen(true)}
            notifications={notifications}
            unreadNotificationCount={unreadNotificationCount}
            onMarkNotificationRead={onMarkNotificationRead}
            onMarkAllNotificationsRead={onMarkAllNotificationsRead}
            onSearch={onSearch}
            userDisplayName={userDisplayName}
            userEmail={userEmail}
            onSignOut={onSignOut}
          />

          {/* Quick Mobile Navigation Bar */}
          <nav
            aria-label="Mobile navigation"
            className="flex gap-2 overflow-x-auto border-b border-[var(--border)] bg-[var(--surface)] px-4 py-2 lg:hidden shadow-xs"
          >
            {mobileNavItems.map((item) => {
              const active =
                item.href === "/"
                  ? pathname === "/"
                  : pathname === item.href || pathname.startsWith(`${item.href}/`);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={[
                    "whitespace-nowrap rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                    active
                      ? "bg-blue-50 font-semibold text-blue-700"
                      : "text-[var(--muted)] hover:bg-[var(--surface-muted)] hover:text-[var(--foreground)]",
                  ].join(" ")}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <main
            id="main-content"
            tabIndex={-1}
            className="mx-auto w-full max-w-[90rem] flex-1 p-4 sm:p-6 lg:p-8 outline-none"
          >
            <Breadcrumbs />
            {children}
          </main>

          <footer className="mt-auto border-t border-[var(--border)] bg-[var(--surface)] py-4">
            <div className="mx-auto max-w-[90rem] px-4 text-center text-xs text-[var(--muted)]">
              AEGIS-DocIntel · Document Intelligence Workbench · Sovereign Human Governance
            </div>
          </footer>
        </div>
      </div>

      {/* Slide-out Drawer for Mobile */}
      <MobileNavigation
        open={mobileOpen}
        permissions={permissions}
        onClose={closeMobile}
      />
    </>
  );
}

export function AppShell(props: AppShellProps) {
  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--foreground)] flex flex-col font-sans">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <Suspense fallback={<ShellSkeleton />}>
        <AppShellInner {...props} />
      </Suspense>
    </div>
  );
}
