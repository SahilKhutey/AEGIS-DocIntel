import type { Permission } from "./permissions";

export type RouteDefinition = {
  id: string;
  path: string;
  name: string;
  requiredPermissions: Permission[];
  status: "active" | "planned";
  authenticationRequired: boolean;
};

export const ROUTES: RouteDefinition[] = [
  {
    id: "overview",
    path: "/",
    name: "Workspace Overview",
    requiredPermissions: ["workspace.read"],
    status: "active",
    authenticationRequired: true,
  },
  {
    id: "documents",
    path: "/documents",
    name: "Document Library",
    requiredPermissions: ["documents.read"],
    status: "active",
    authenticationRequired: true,
  },
  {
    id: "document-detail",
    path: "/documents/[documentId]",
    name: "Document Inspection",
    requiredPermissions: ["documents.read"],
    status: "active",
    authenticationRequired: true,
  },
  {
    id: "ask",
    path: "/ask",
    name: "Ask AEGIS",
    requiredPermissions: ["intelligence.query"],
    status: "active",
    authenticationRequired: true,
  },
  {
    id: "compare",
    path: "/compare",
    name: "Document Comparison",
    requiredPermissions: ["documents.compare"],
    status: "active",
    authenticationRequired: true,
  },
  {
    id: "reviews",
    path: "/reviews",
    name: "Review Queue",
    requiredPermissions: ["governance.read"],
    status: "active",
    authenticationRequired: true,
  },
  {
    id: "review-detail",
    path: "/reviews/[reviewId]",
    name: "Review Details",
    requiredPermissions: ["governance.review"],
    status: "active",
    authenticationRequired: true,
  },
  {
    id: "evidence",
    path: "/evidence",
    name: "Evidence Explorer",
    requiredPermissions: ["evidence.read"],
    status: "planned",
    authenticationRequired: true,
  },
  {
    id: "processing",
    path: "/processing",
    name: "Processing Monitor",
    requiredPermissions: ["processing.read"],
    status: "planned",
    authenticationRequired: true,
  },
  {
    id: "analytics",
    path: "/analytics",
    name: "Analytics",
    requiredPermissions: ["workspace.read"],
    status: "planned",
    authenticationRequired: true,
  },
  {
    id: "settings",
    path: "/settings",
    name: "Settings",
    requiredPermissions: ["workspace.settings.manage"],
    status: "planned",
    authenticationRequired: true,
  },
  {
    id: "integrations",
    path: "/integrations",
    name: "Integrations",
    requiredPermissions: ["integrations.manage"],
    status: "planned",
    authenticationRequired: true,
  },
];
