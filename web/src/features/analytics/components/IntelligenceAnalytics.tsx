import React from "react";
import type { TenantStats, TokenUsageData } from "../types";
import { Zap, Cpu } from "lucide-react";

export interface IntelligenceAnalyticsProps {
  stats: TenantStats;
  tokenUsage?: TokenUsageData;
}

export const IntelligenceAnalytics: React.FC<IntelligenceAnalyticsProps> = ({
  stats,
  tokenUsage,
}) => {
  const promptTokens = tokenUsage?.prompt_tokens ?? Math.round(stats.total_tokens_used * 0.78);
  const completionTokens = tokenUsage?.completion_tokens ?? Math.round(stats.total_tokens_used * 0.22);
  const promptPct = stats.total_tokens_used > 0 ? (promptTokens / stats.total_tokens_used) * 100 : 0;
  const completionPct = stats.total_tokens_used > 0 ? (completionTokens / stats.total_tokens_used) * 100 : 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <h3 className="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-500" aria-hidden="true" />
          <span>Token Consumption Breakdown</span>
        </h3>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-600 font-medium">Prompt / Context Tokens</span>
              <span className="font-semibold text-slate-900">{promptTokens.toLocaleString()} ({promptPct.toFixed(1)}%)</span>
            </div>
            <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
              <div className="bg-amber-500 h-2.5 rounded-full" style={{ width: `${promptPct}%` }} />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-600 font-medium">Completion / Synthesis Tokens</span>
              <span className="font-semibold text-slate-900">{completionTokens.toLocaleString()} ({completionPct.toFixed(1)}%)</span>
            </div>
            <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
              <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${completionPct}%` }} />
            </div>
          </div>
          <div className="pt-3 border-t border-slate-100 flex justify-between text-xs">
            <span className="text-slate-500">Total Tokens Evaluated</span>
            <span className="font-bold text-slate-900">{stats.total_tokens_used.toLocaleString()}</span>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <h3 className="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-emerald-600" aria-hidden="true" />
          <span>Model Distribution & Routing</span>
        </h3>
        {tokenUsage?.model_breakdowns ? (
          <div className="space-y-3">
            {Object.entries(tokenUsage.model_breakdowns).map(([model, tokens]) => {
              const pct = stats.total_tokens_used > 0 ? (tokens / stats.total_tokens_used) * 100 : 0;
              return (
                <div key={model}>
                  <div className="flex justify-between text-xs mb-1 font-mono">
                    <span className="text-slate-700 font-medium truncate">{model}</span>
                    <span className="text-slate-500">{tokens.toLocaleString()} ({pct.toFixed(0)}%)</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-slate-500">No model breakdown available for this period.</p>
        )}
      </div>
    </div>
  );
};
