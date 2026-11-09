"use client";

import React, { useState, useEffect } from "react";
import { getIntegrationConnectors } from "../api/developer.api";
import type { IntegrationConnector } from "../types";
import { CheckCircle2, RefreshCw, Layers, Database, HardDrive, Key } from "lucide-react";

export const IntegrationStatusCard: React.FC = () => {
  const [connectors, setConnectors] = useState<IntegrationConnector[]>([]);
  const [testingId, setTestingId] = useState<string | null>(null);

  useEffect(() => {
    getIntegrationConnectors().then(setConnectors);
  }, []);

  const handleTestConnection = async (id: string) => {
    setTestingId(id);
    await new Promise((resolve) => setTimeout(resolve, 600));
    setTestingId(null);
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "storage":
        return <HardDrive className="w-4 h-4 text-purple-600" aria-hidden="true" />;
      case "database":
        return <Database className="w-4 h-4 text-blue-600" aria-hidden="true" />;
      case "identity":
        return <Key className="w-4 h-4 text-emerald-600" aria-hidden="true" />;
      default:
        return <Layers className="w-4 h-4 text-slate-500" aria-hidden="true" />;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-bold text-slate-900">External Integrations & Connectors</h3>
          <p className="text-xs text-slate-500">
            Verify network connectivity and authentication tokens for backing object stores, databases, and OAuth providers.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {connectors.map((conn) => {
          const isTesting = testingId === conn.id;
          return (
            <div
              key={conn.id}
              className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white transition-all space-y-3"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-white border border-slate-200 shadow-2xs">
                    {getCategoryIcon(conn.category)}
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">{conn.name}</h4>
                    <span className="text-[10px] text-slate-400 font-sans block">{conn.provider}</span>
                  </div>
                </div>

                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
                  <span>Connected</span>
                </span>
              </div>

              <div className="p-2 rounded bg-white border border-slate-100 text-[11px] font-mono text-slate-600 truncate">
                {conn.endpoint}
              </div>

              <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-200/60">
                <span className="text-slate-500 font-mono text-[11px]">
                  Latency: <span className="font-bold text-slate-800">{conn.latencyMs}ms</span>
                </span>

                <button
                  type="button"
                  onClick={() => handleTestConnection(conn.id)}
                  disabled={isTesting}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-white hover:bg-slate-50 border border-slate-200 text-xs font-medium text-slate-700 shadow-2xs cursor-pointer disabled:opacity-50"
                >
                  <RefreshCw className={`w-3 h-3 ${isTesting ? "animate-spin text-blue-600" : ""}`} aria-hidden="true" />
                  <span>{isTesting ? "Testing..." : "Test Ping"}</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
