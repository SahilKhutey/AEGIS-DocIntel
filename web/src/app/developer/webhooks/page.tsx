import React from "react";
import { DeveloperHub } from "@/features/developer/components/DeveloperHub";

export const metadata = {
  title: "Webhook Subscriptions — AEGIS-DocIntel",
  description: "Outbound event dispatching with SSRF protection and delivery logs",
};

export default function DeveloperWebhooksPage() {
  return (
    <div className="space-y-6">
      <DeveloperHub initialTab="webhooks" />
    </div>
  );
}
