"use client";

import React, { useState, useEffect } from "react";
import { getMonitoringSnapshot } from "../api/monitoring.api";
import type { MonitoringSnapshot } from "../types";
import { ServiceHealthList } from "./ServiceHealthList";
import { LatencyPercentiles } from "./LatencyPercentiles";
import { ThroughputChart } from "./ThroughputChart";
import { AlertsList } from "./AlertsList";
import { FreshnessBadge } from "./FreshnessBadge";
import { ShieldCheck } from "lucide-react";

export const MonitoringDashboard: React.FC = () => {
  const [snapshot, setSnapshot] = useState<MonitoringSnapshot | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const data = await getMonitoringSnapshot();
      setSnapshot(data);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-lg font-bold text-slate-900">System Health & Performance Monitoring</h2>
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <ShieldCheck className="w-3.5 h-3.5" aria-hidden="true" />
              <span>All Systems Operational</span>
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Real-time telemetry of API gateway, vector store, blob storage, queue latency, and SLAs.
          </p>
        </div>

        {snapshot && (
          <FreshnessBadge
            lastUpdated={snapshot.timestamp}
            onRefresh={loadData}
            isLoading={isLoading}
          />
        )}
      </div>

      {snapshot && (
        <div className="space-y-6">
          <ServiceHealthList services={snapshot.services} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <LatencyPercentiles percentiles={snapshot.latencyPercentiles} />
            <ThroughputChart metrics={snapshot.throughput} />
          </div>

          <AlertsList initialAlerts={snapshot.alerts} />
        </div>
      )}
    </div>
  );
};
