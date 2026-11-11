export type BreadcrumbDefinition = {
  label: string;
  href?: string;
};

const ROUTE_BREADCRUMBS: Record<string, BreadcrumbDefinition[]> = {
  "/": [
    { label: "Workspace" },
    { label: "Overview" },
  ],

  "/documents": [
    { label: "Workspace", href: "/" },
    { label: "Documents" },
  ],

  "/ask": [
    { label: "Workspace", href: "/" },
    { label: "Intelligence" },
    { label: "Ask AEGIS" },
  ],

  "/compare": [
    { label: "Workspace", href: "/" },
    { label: "Intelligence" },
    { label: "Compare documents" },
  ],

  "/reviews": [
    { label: "Workspace", href: "/" },
    { label: "Governance" },
    { label: "Reviews" },
  ],

  "/analytics": [
    { label: "Workspace", href: "/" },
    { label: "Operations" },
    { label: "Analytics" },
  ],

  "/mathematics": [
    { label: "Workspace", href: "/" },
    { label: "Operations" },
    { label: "Mathematics" },
  ],

  "/pipelines": [
    { label: "Workspace", href: "/" },
    { label: "Operations" },
    { label: "Pipelines" },
  ],

  "/monitoring": [
    { label: "Workspace", href: "/" },
    { label: "Operations" },
    { label: "Monitoring" },
  ],

  "/developer": [
    { label: "Workspace", href: "/" },
    { label: "Developer" },
  ],
};

export function getBreadcrumbs(pathname: string): BreadcrumbDefinition[] {
  if (ROUTE_BREADCRUMBS[pathname]) {
    return ROUTE_BREADCRUMBS[pathname];
  }

  if (pathname.startsWith("/documents/")) {
    return [
      { label: "Workspace", href: "/" },
      { label: "Documents", href: "/documents" },
      { label: "Document details" },
    ];
  }

  if (pathname.startsWith("/reviews/")) {
    return [
      { label: "Workspace", href: "/" },
      { label: "Reviews", href: "/reviews" },
      { label: "Review details" },
    ];
  }

  if (pathname.startsWith("/pipelines/")) {
    return [
      { label: "Workspace", href: "/" },
      { label: "Pipelines", href: "/pipelines" },
      { label: "Pipeline Run" },
    ];
  }

  if (pathname.startsWith("/mathematics/")) {
    return [
      { label: "Workspace", href: "/" },
      { label: "Mathematics", href: "/mathematics" },
      { label: "Representation" },
    ];
  }

  return [{ label: "Workspace", href: "/" }, { label: "Page" }];
}
