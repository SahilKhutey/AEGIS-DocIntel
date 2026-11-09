"use client";

import React, { useState } from "react";
import type { OperationalAlert } from "../types";
import { AlertCircle, AlertTriangle, Info, Check } from "lucide-react";

export interface AlertsListProps {
  initialAlerts: OperationalAlert[];
}

export const AlertsList: React.FC<AlertsListProps> = ({ initialAlerts }) => {
  const [alerts, setAlerts] = useState<OperationalAlert[]>(initialAlerts);

  const handleAcknowledge = (id: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, acknowledged: true } : a)),
    );
  };

  const activeAlerts = alerts.filter((a) => !a.acknowledged);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-slate-600" aria-hidden="true" />
          <h3 className="text-sm font-bold text-slate-900">Operational Alerts & Notifications</h3>
        </div>
        <span className="text-xs text-slate-500 font-medium">
          {activeAlerts.length} active
        </span>
      </div>

      {activeAlerts.length === 0 ? (
        <div className="p-4 rounded-lg bg-emerald-50/50 border border-emerald-100 text-xs text-emerald-800 flex items-center gap-2">
          <Check className="w-4 h-4 text-emerald-600" aria-hidden="true" />
          <span>All systems operating within acceptable parameters. No unacknowledged alerts.</span>
        </div>
      ) : (
        <div className="space-y-3">
          {activeAlerts.map((alert) => {
            let badgeBg = "bg-blue-50 text-blue-700 border-blue-200";
            let Icon = Info;
            if (alert.severity === "critical") {
              badgeBg = "bg-rose-50 text-rose-700 border-rose-200";
              Icon = AlertCircle;
            } else if (alert.severity === "warning") {
              badgeBg = "bg-amber-50 text-amber-700 border-amber-200";
              Icon = AlertTriangle;
            }

            return (
              <div
                key={alert.id}
                className={`p-3.5 rounded-lg border flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 ${badgeBg}`}
              >
                <div className="flex items-start gap-2.5">
                  <Icon className="w-4 h-4 mt-0.5 shrink-0" aria-hidden="true" />
                  <div>
                    <h4 className="text-xs font-bold">{alert.title}</h4>
                    <p className="text-[11px] opacity-90 mt-0.5">{alert.message}</p>
                    <span className="text-[10px] opacity-75 font-mono block mt-1">
                      {new Date(alert.timestamp).toLocaleTimeString()} · Source: {alert.serviceId}
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => handleAcknowledge(alert.id)}
                  className="px-2.5 py-1 rounded bg-white/80 hover:bg-white text-xs font-medium text-slate-800 border border-slate-200 shadow-2xs self-end sm:self-center cursor-pointer"
                >
                  Acknowledge
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
