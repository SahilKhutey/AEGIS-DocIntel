import React from "react";
import { MonitoringDashboard } from "@/features/monitoring/components/MonitoringDashboard";

export const metadata = {
  title: "Performance Monitoring — AEGIS-DocIntel",
  description: "Live system health, query latency percentiles, throughput, and operational alerts",
};

export default function MonitoringPage() {
  return (
    <div className="space-y-6">
      <MonitoringDashboard />
    </div>
  );
}
