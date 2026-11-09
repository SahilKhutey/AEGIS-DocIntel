"use client";

import { Menu, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { WorkspaceSelector } from "./workspace-selector";
import { NotificationCenter } from "./notification-center";
import { GlobalSearch } from "./global-search";
import { UserMenu } from "./user-menu";
import type { Workspace } from "@/features/workspaces/types";
import type { Notification } from "@/features/notifications/types";
import type { GlobalSearchResponse } from "@/features/search/types";

type AppHeaderProps = {
  workspaces?: Workspace[];
  activeWorkspaceId?: string;
  onWorkspaceSelect?: (id: string) => Promise<void>;
  onMenuClick: () => void;
  notifications?: Notification[];
  unreadNotificationCount?: number;
  onMarkNotificationRead?: (id: string) => Promise<void>;
  onMarkAllNotificationsRead?: () => Promise<void>;
  onSearch?: (query: string) => Promise<GlobalSearchResponse>;
  userDisplayName?: string;
  userEmail?: string;
  onSignOut?: () => Promise<void>;
};

export function AppHeader({
  workspaces,
  activeWorkspaceId,
  onWorkspaceSelect,
  onMenuClick,
  notifications,
  unreadNotificationCount,
  onMarkNotificationRead,
  onMarkAllNotificationsRead,
  onSearch,
  userDisplayName,
  userEmail,
  onSignOut,
}: AppHeaderProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-3 border-b border-[var(--border)] bg-[var(--surface)] px-4 sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <Button
          variant="ghost"
          size="sm"
          className="lg:hidden h-9 w-9 p-0 text-[var(--muted)] hover:text-[var(--foreground)]"
          aria-label="Open navigation"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </Button>

        <WorkspaceSelector
          workspaces={workspaces}
          activeWorkspaceId={activeWorkspaceId}
          onSelect={onWorkspaceSelect}
        />
      </div>

      <div className="hidden min-w-0 flex-1 justify-center max-w-xl mx-4 md:flex">
        <GlobalSearch search={onSearch} />
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          className="md:hidden h-9 w-9 p-0 text-[var(--muted)] hover:text-[var(--foreground)]"
          aria-label="Open search"
          onClick={() => {
            window.dispatchEvent(new Event("aegis:open-search"));
          }}
        >
          <Search className="h-5 w-5" aria-hidden="true" />
        </Button>

        <NotificationCenter
          items={notifications}
          unreadCount={unreadNotificationCount}
          onMarkRead={onMarkNotificationRead}
          onMarkAllRead={onMarkAllNotificationsRead}
        />

        <UserMenu
          displayName={userDisplayName}
          email={userEmail}
          onSignOut={onSignOut}
        />
      </div>
    </header>
  );
}
