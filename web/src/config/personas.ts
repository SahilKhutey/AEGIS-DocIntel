import type { ProductRole } from "./permissions";

export type Persona = {
  id: ProductRole;
  title: string;
  summary: string;
  goals: string[];
  primaryRoutes: string[];
};

export const PERSONAS: Record<ProductRole, Persona> = {
  workspace_user: {
    id: "workspace_user",
    title: "Workspace User",
    summary: "Manages and understands authorized documents.",
    goals: [
      "Upload documents",
      "Locate relevant information",
      "Monitor document processing",
    ],
    primaryRoutes: ["/", "/documents", "/ask"],
  },
  analyst: {
    id: "analyst",
    title: "Intelligence Analyst",
    summary: "Investigates documents and supporting evidence.",
    goals: [
      "Query authorized document collections",
      "Compare source documents",
      "Investigate evidence and conflicts",
    ],
    primaryRoutes: ["/documents", "/ask", "/compare"],
  },
  reviewer: {
    id: "reviewer",
    title: "Governance Reviewer",
    summary: "Validates candidate facts and governance decisions.",
    goals: [
      "Inspect candidate facts",
      "Verify supporting evidence",
      "Submit review decisions",
    ],
    primaryRoutes: ["/reviews", "/documents"],
  },
  administrator: {
    id: "administrator",
    title: "Workspace Administrator",
    summary: "Administers workspace access and configuration.",
    goals: [
      "Manage workspace users",
      "Review security and configuration",
      "Maintain workspace settings",
    ],
    primaryRoutes: ["/", "/settings"],
  },
  developer: {
    id: "developer",
    title: "Developer / Integrator",
    summary: "Integrates AEGIS with external systems.",
    goals: [
      "Understand API capabilities",
      "Manage authorized integrations",
      "Diagnose integration issues",
    ],
    primaryRoutes: ["/integrations"],
  },
};
