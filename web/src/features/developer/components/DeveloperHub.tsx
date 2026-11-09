"use client";

import React, { useState } from "react";
import { ApiCredentialManager } from "./ApiCredentialManager";
import { WebhookManager } from "./WebhookManager";
import { ApiExplorer } from "./ApiExplorer";
import { IntegrationStatusCard } from "./IntegrationStatusCard";
import { Code, Key, Webhook, Layers } from "lucide-react";

export type DeveloperTab = "keys" | "api" | "webhooks" | "integrations";

export interface DeveloperHubProps {
  initialTab?: DeveloperTab;
}

export const DeveloperHub: React.FC<DeveloperHubProps> = ({ initialTab = "keys" }) => {
  const [activeTab, setActiveTab] = useState<DeveloperTab>(initialTab);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Developer Platform & Integration Center</h2>
          <p className="text-xs text-slate-500">
            OpenAPI references, API key management, SSRF-validated webhooks, and enterprise backing connectors.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded bg-slate-100 border border-slate-200 text-xs font-mono text-slate-700">
            OpenAPI 3.1
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6" aria-label="Developer Sections">
          <button
            type="button"
            onClick={() => setActiveTab("keys")}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "keys"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
          >
            <Key className="w-4 h-4" aria-hidden="true" />
            <span>API Credentials</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("api")}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "api"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
          >
            <Code className="w-4 h-4" aria-hidden="true" />
            <span>API Explorer</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("webhooks")}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "webhooks"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
          >
            <Webhook className="w-4 h-4" aria-hidden="true" />
            <span>Webhooks</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("integrations")}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "integrations"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
          >
            <Layers className="w-4 h-4" aria-hidden="true" />
            <span>Integrations</span>
          </button>
        </nav>
      </div>

      {/* Panels */}
      {activeTab === "keys" && <ApiCredentialManager />}
      {activeTab === "api" && <ApiExplorer />}
      {activeTab === "webhooks" && <WebhookManager />}
      {activeTab === "integrations" && <IntegrationStatusCard />}
    </div>
  );
};
