import React from "react";
import { DeveloperHub } from "@/features/developer/components/DeveloperHub";

export const metadata = {
  title: "External Integrations — AEGIS-DocIntel",
  description: "Connectors for object storage, PostgreSQL, vector database, and identity",
};

export default function DeveloperIntegrationsPage() {
  return (
    <div className="space-y-6">
      <DeveloperHub initialTab="integrations" />
    </div>
  );
}
