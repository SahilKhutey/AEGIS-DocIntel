import React from "react";
import { AnalyticsDashboard } from "@/features/analytics/components/AnalyticsDashboard";

export const metadata = {
  title: "Analytics & Reporting — AEGIS-DocIntel",
  description: "Operational KPIs, token usage, query latency, and governance review throughput",
};

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <AnalyticsDashboard />
    </div>
  );
}
