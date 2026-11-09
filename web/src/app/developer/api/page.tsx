import React from "react";
import { DeveloperHub } from "@/features/developer/components/DeveloperHub";

export const metadata = {
  title: "API Explorer — AEGIS-DocIntel",
  description: "Interactive OpenAPI documentation and request code snippets",
};

export default function DeveloperApiPage() {
  return (
    <div className="space-y-6">
      <DeveloperHub initialTab="api" />
    </div>
  );
}
