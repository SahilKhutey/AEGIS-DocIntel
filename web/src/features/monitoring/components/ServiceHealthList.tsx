import React from "react";
import type { ServiceHealthItem, ServiceStatus } from "../types";
import { CheckCircle2, AlertTriangle, XCircle, Server } from "lucide-react";

export interface ServiceHealthListProps {
  services: ServiceHealthItem[];
}

export const ServiceHealthList: React.FC<ServiceHealthListProps> = ({ services }) => {
  const getStatusBadge = (status: ServiceStatus) => {
    switch (status) {
      case "healthy":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Healthy</span>
          </span>
        );
      case "degraded":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Degraded</span>
          </span>
        );
      case "unhealthy":
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Unhealthy</span>
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Server className="w-4 h-4 text-blue-600" aria-hidden="true" />
          <h3 className="text-sm font-bold text-slate-900">Infrastructure & Dependent Services</h3>
        </div>
        <span className="text-xs text-slate-500 font-medium">
          {services.filter((s) => s.status === "healthy").length} / {services.length} services operational
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {services.map((svc) => (
          <div
            key={svc.id}
            className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white transition-all space-y-3"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <h4 className="text-xs font-bold text-slate-900 leading-snug">{svc.name}</h4>
                <span className="text-[10px] text-slate-400 font-mono uppercase">{svc.category}</span>
              </div>
              {getStatusBadge(svc.status)}
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-2 border-t border-slate-200/60">
              <div>
                <span className="text-[10px] text-slate-400 font-sans block">Latency</span>
                <span className="font-bold text-slate-800">{svc.latencyMs}ms</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-sans block">Uptime</span>
                <span className="font-bold text-emerald-700">{svc.uptimePercent}%</span>
              </div>
            </div>

            {svc.details && (
              <p className="text-[11px] text-slate-500 line-clamp-2" title={svc.details}>
                {svc.details}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
