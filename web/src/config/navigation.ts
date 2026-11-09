import type { Permission } from "./permissions";

export type NavigationItem = {
  id: string;
  label: string;
  href: string;
  description: string;
  requiredPermissions: Permission[];
  status: "active" | "planned";
  match: "exact" | "prefix";
};

export type NavigationGroup = {
  id: string;
  label: string;
  items: NavigationItem[];
};

export const NAVIGATION: NavigationGroup[] = [
  {
    id: "workspace",
    label: "Workspace",
    items: [
      {
        id: "overview",
        label: "Overview",
        href: "/",
        description: "Workspace overview",
        requiredPermissions: ["workspace.read"],
        status: "active",
        match: "exact",
      },
    ],
  },
  {
    id: "documents",
    label: "Documents",
    items: [
      {
        id: "document-library",
        label: "Document Library",
        href: "/documents",
        description: "Browse and manage authorized documents",
        requiredPermissions: ["documents.read"],
        status: "active",
        match: "prefix",
      },
    ],
  },
  {
    id: "intelligence",
    label: "Intelligence",
    items: [
      {
        id: "ask",
        label: "Ask AEGIS",
        href: "/ask",
        description: "Ask questions over authorized sources",
        requiredPermissions: ["intelligence.query"],
        status: "active",
        match: "prefix",
      },
      {
        id: "compare",
        label: "Compare Documents",
        href: "/compare",
        description: "Compare authorized documents",
        requiredPermissions: ["documents.compare"],
        status: "active",
        match: "prefix",
      },
      {
        id: "evidence",
        label: "Evidence Explorer",
        href: "/evidence",
        description: "Explore evidence across documents",
        requiredPermissions: ["evidence.read"],
        status: "planned",
        match: "prefix",
      },
    ],
  },
  {
    id: "governance",
    label: "Governance",
    items: [
      {
        id: "reviews",
        label: "Review Queue",
        href: "/reviews",
        description: "Inspect and review candidate facts",
        requiredPermissions: ["governance.read"],
        status: "active",
        match: "prefix",
      },
    ],
  },
  {
    id: "system",
    label: "System",
    items: [
      {
        id: "processing",
        label: "Processing Jobs",
        href: "/processing",
        description: "Monitor document processing",
        requiredPermissions: ["processing.read"],
        status: "planned",
        match: "prefix",
      },
      {
        id: "analytics",
        label: "Analytics",
        href: "/analytics",
        description: "Inspect system metrics",
        requiredPermissions: ["workspace.read"],
        status: "planned",
        match: "prefix",
      },
      {
        id: "settings",
        label: "Settings",
        href: "/settings",
        description: "Manage workspace configuration",
        requiredPermissions: ["workspace.settings.manage"],
        status: "planned",
        match: "prefix",
      },
      {
        id: "integrations",
        label: "Integrations",
        href: "/integrations",
        description: "Manage external integrations",
        requiredPermissions: ["integrations.manage"],
        status: "planned",
        match: "prefix",
      },
    ],
  },
];

export function isNavigationItemActive(
  pathname: string,
  item: NavigationItem,
): boolean {
  if (item.status !== "active") return false;

  if (item.match === "exact") {
    return pathname === item.href;
  }

  return (
    pathname === item.href ||
    pathname.startsWith(`${item.href}/`)
  );
}

export function getActiveNavigationItem(pathname: string) {
  return NAVIGATION
    .flatMap((group) => group.items)
    .find((item) => isNavigationItemActive(pathname, item));
}
