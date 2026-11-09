export type NavigationStatus = "active" | "planned";

export type NavigationItem = {
  label: string;
  href: string;
  description: string;
  status: NavigationStatus;
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
        label: "Overview",
        href: "/",
        description: "Workspace overview and entry point",
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
        label: "Document Library",
        href: "/documents",
        description: "Browse, upload and inspect documents",
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
        label: "Ask AEGIS",
        href: "/ask",
        description: "Ask questions over authorized sources",
        status: "active",
        match: "prefix",
      },
      {
        label: "Compare Documents",
        href: "/compare",
        description: "Compare documents and identify differences",
        status: "active",
        match: "prefix",
      },
      {
        label: "Evidence Explorer",
        href: "/evidence",
        description: "Explore evidence across documents",
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
        label: "Review Queue",
        href: "/reviews",
        description: "Review candidate facts and conflicts",
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
        label: "Processing Jobs",
        href: "/processing",
        description: "Monitor document processing jobs",
        status: "planned",
        match: "prefix",
      },
      {
        label: "Analytics",
        href: "/analytics",
        description: "Inspect system and quality metrics",
        status: "planned",
        match: "prefix",
      },
      {
        label: "Settings",
        href: "/settings",
        description: "Manage workspace configuration",
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
