export type ShellNavigationItem = {
  id: string;
  label: string;
  href: string;
  icon: string;
  requiredPermissions: string[];
  status: "active" | "planned";
};

export type ShellNavigationGroup = {
  id: string;
  label: string;
  items: ShellNavigationItem[];
};

export const SHELL_NAVIGATION: ShellNavigationGroup[] = [
  {
    id: "workspace",
    label: "Workspace",
    items: [
      {
        id: "overview",
        label: "Overview",
        href: "/",
        icon: "layout-dashboard",
        requiredPermissions: ["workspace.read"],
        status: "active",
      },
    ],
  },
  {
    id: "documents",
    label: "Documents",
    items: [
      {
        id: "documents-list",
        label: "Document Library",
        href: "/documents",
        icon: "files",
        requiredPermissions: ["documents.read"],
        status: "active",
      },
      {
        id: "processing",
        label: "Processing",
        href: "/processing",
        icon: "workflow",
        requiredPermissions: ["processing.read"],
        status: "planned",
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
        icon: "message-square",
        requiredPermissions: ["intelligence.query"],
        status: "active",
      },
      {
        id: "compare",
        label: "Compare Documents",
        href: "/compare",
        icon: "git-compare",
        requiredPermissions: ["documents.compare"],
        status: "active",
      },
      {
        id: "evidence",
        label: "Evidence explorer",
        href: "/evidence",
        icon: "file-search",
        requiredPermissions: ["evidence.read"],
        status: "planned",
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
        icon: "clipboard-check",
        requiredPermissions: ["governance.read"],
        status: "active",
      },
      {
        id: "analytics",
        label: "Analytics",
        href: "/analytics",
        icon: "chart-no-axes-combined",
        requiredPermissions: ["workspace.read"],
        status: "planned",
      },
    ],
  },
  {
    id: "product",
    label: "Product & Launch",
    items: [
      {
        id: "features",
        label: "Features & Architecture",
        href: "/features",
        icon: "file-search",
        requiredPermissions: ["workspace.read"],
        status: "active",
      },
      {
        id: "demo",
        label: "75s Walkthrough",
        href: "/demo",
        icon: "workflow",
        requiredPermissions: ["workspace.read"],
        status: "active",
      },
      {
        id: "security",
        label: "Security & Trust",
        href: "/security",
        icon: "clipboard-check",
        requiredPermissions: ["workspace.read"],
        status: "active",
      },
      {
        id: "evaluation",
        label: "Evaluation Portal",
        href: "/evaluation",
        icon: "plug",
        requiredPermissions: ["workspace.read"],
        status: "active",
      },
    ],
  },
  {
    id: "system",
    label: "System",
    items: [
      {
        id: "integrations",
        label: "Integrations",
        href: "/integrations",
        icon: "plug",
        requiredPermissions: ["integrations.manage"],
        status: "planned",
      },
      {
        id: "settings",
        label: "Settings",
        href: "/settings",
        icon: "settings",
        requiredPermissions: ["workspace.settings.manage"],
        status: "planned",
      },
    ],
  },
];
