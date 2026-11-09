import React from "react";
import { DeveloperHub } from "@/features/developer/components/DeveloperHub";

export const metadata = {
  title: "Developer Platform — AEGIS-DocIntel",
  description: "API explorer, credentials, webhooks, and integrations",
};

export default function DeveloperPage() {
  return (
    <div className="space-y-6">
      <DeveloperHub initialTab="keys" />
    </div>
  );
}
