export type RouteDefinition = {
  path: string;
  name: string;
  capability: string;
  status: "active" | "planned";
  requiresAuthentication: boolean;
};

export const ROUTES: RouteDefinition[] = [
  {
    path: "/",
    name: "Workspace Overview",
    capability: "workspace.read",
    status: "active",
    requiresAuthentication: true,
  },
  {
    path: "/documents",
    name: "Document Library",
    capability: "documents.read",
    status: "active",
    requiresAuthentication: true,
  },
  {
    path: "/documents/[documentId]",
    name: "Document Inspection",
    capability: "documents.read",
    status: "active",
    requiresAuthentication: true,
  },
  {
    path: "/ask",
    name: "Ask AEGIS",
    capability: "intelligence.query",
    status: "active",
    requiresAuthentication: true,
  },
  {
    path: "/compare",
    name: "Document Comparison",
    capability: "documents.compare",
    status: "active",
    requiresAuthentication: true,
  },
  {
    path: "/reviews",
    name: "Review Queue",
    capability: "governance.read",
    status: "active",
    requiresAuthentication: true,
  },
  {
    path: "/reviews/[reviewId]",
    name: "Review Details",
    capability: "governance.review",
    status: "active",
    requiresAuthentication: true,
  },
  {
    path: "/processing",
    name: "Processing Monitor",
    capability: "processing.read",
    status: "planned",
    requiresAuthentication: true,
  },
  {
    path: "/evidence",
    name: "Evidence Explorer",
    capability: "evidence.read",
    status: "planned",
    requiresAuthentication: true,
  },
  {
    path: "/analytics",
    name: "Analytics",
    capability: "analytics.read",
    status: "planned",
    requiresAuthentication: true,
  },
  {
    path: "/settings",
    name: "Settings",
    capability: "settings.read",
    status: "planned",
    requiresAuthentication: true,
  },
];
