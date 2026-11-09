"use client";

import React, { useState } from "react";
import { useAnalytics } from "../hooks/useAnalytics";
import { TimeRangeSelector } from "@/components/advanced/TimeRangeSelector";
import { OverviewMetrics } from "./OverviewMetrics";
import { DocumentAnalytics } from "./DocumentAnalytics";
import { IntelligenceAnalytics } from "./IntelligenceAnalytics";
import { GovernanceAnalytics } from "./GovernanceAnalytics";
import { Download, RefreshCw, BarChart2, FileText, Zap, ShieldCheck } from "lucide-react";

export type AnalyticsTab = "overview" | "documents" | "intelligence" | "governance";

export const AnalyticsDashboard: React.FC = () => {
  const { timeRange, setTimeRange, data, isLoading, error, refresh, exportCsv } = useAnalytics();
  const [activeTab, setActiveTab] = useState<AnalyticsTab>("overview");

  return (
    <div className="space-y-6">
      {/* Top Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Analytics & Operational Metrics</h2>
          <p className="text-xs text-slate-500">
            Real-time observability of ingestion, intelligence inference, costs, and human governance.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <TimeRangeSelector
            value={timeRange}
            onChange={setTimeRange}
            disabled={isLoading}
          />

          <button
            type="button"
            onClick={refresh}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 min-h-[28px] text-xs font-medium rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50 cursor-pointer"
            aria-label="Refresh metrics"
            title="Refresh metrics"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-blue-600" : ""}`} aria-hidden="true" />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            onClick={exportCsv}
            disabled={isLoading || !data}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 min-h-[28px] text-xs font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 cursor-pointer shadow-xs"
          >
            <Download className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {error && (
        <div role="alert" className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800">
          Failed to load analytics: {error}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6" aria-label="Analytics Sections">
          <button
            type="button"
            onClick={() => setActiveTab("overview")}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "overview"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
            aria-current={activeTab === "overview" ? "page" : undefined}
          >
            <BarChart2 className="w-4 h-4" aria-hidden="true" />
            <span>Overview KPIs</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("documents")}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "documents"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
            aria-current={activeTab === "documents" ? "page" : undefined}
          >
            <FileText className="w-4 h-4" aria-hidden="true" />
            <span>Documents & Ingestion</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("intelligence")}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "intelligence"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
            aria-current={activeTab === "intelligence" ? "page" : undefined}
          >
            <Zap className="w-4 h-4" aria-hidden="true" />
            <span>Intelligence & Tokens</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("governance")}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "governance"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
            aria-current={activeTab === "governance" ? "page" : undefined}
          >
            <ShieldCheck className="w-4 h-4" aria-hidden="true" />
            <span>Governance Reviews</span>
          </button>
        </nav>
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === "overview" && data && (
          <div className="space-y-6">
            <OverviewMetrics
              stats={data.stats}
              previousStats={data.previousStats}
              isLoading={isLoading}
            />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <DocumentAnalytics stats={data.stats} />
              <IntelligenceAnalytics stats={data.stats} tokenUsage={data.tokenUsage} />
            </div>
          </div>
        )}

        {activeTab === "documents" && data && (
          <DocumentAnalytics stats={data.stats} />
        )}

        {activeTab === "intelligence" && data && (
          <IntelligenceAnalytics stats={data.stats} tokenUsage={data.tokenUsage} />
        )}

        {activeTab === "governance" && data && (
          <GovernanceAnalytics
            metrics={data.governanceMetrics}
            previousMetrics={data.previousGovernanceMetrics}
          />
        )}
      </div>
    </div>
  );
};
