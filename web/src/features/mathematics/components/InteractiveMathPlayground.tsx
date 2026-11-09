"use client";

import React, { useState } from "react";
import { evaluateUnifiedMath, checkTopologyPercolation } from "../api/mathematics.api";
import type { TopologyData } from "../types";
import { Calculator, Play, Network, CheckCircle } from "lucide-react";

export const InteractiveMathPlayground: React.FC = () => {
  const [expression, setExpression] = useState("cos_sim(u, v) * 0.85 + bm25_score * 0.15");
  const [result, setResult] = useState<number | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [topology, setTopology] = useState<TopologyData | null>(null);
  const [isLoadingTopology, setIsLoadingTopology] = useState(false);

  const handleEvaluate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsEvaluating(true);
    try {
      const res = await evaluateUnifiedMath(expression);
      setResult(res.result);
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleCheckTopology = async () => {
    setIsLoadingTopology(true);
    try {
      const topo = await checkTopologyPercolation();
      setTopology(topo);
    } finally {
      setIsLoadingTopology(false);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Expression Evaluator */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <div className="flex items-center gap-2">
          <Calculator className="w-4 h-4 text-blue-600" aria-hidden="true" />
          <h3 className="text-sm font-bold text-slate-900">Unified Math Evaluation</h3>
        </div>
        <p className="text-xs text-slate-500">
          Compute verified scoring combinations and similarity metrics via backend mathematical solver.
        </p>

        <form onSubmit={handleEvaluate} className="space-y-3">
          <div>
            <label htmlFor="math-expr" className="block text-xs font-medium text-slate-700 mb-1">
              Mathematical Expression
            </label>
            <input
              id="math-expr"
              type="text"
              value={expression}
              onChange={(e) => setExpression(e.target.value)}
              className="w-full px-3 py-2 text-xs font-mono rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. sqrt(a^2 + b^2)"
            />
          </div>

          <button
            type="submit"
            disabled={isEvaluating}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium cursor-pointer shadow-xs disabled:opacity-50"
          >
            <Play className="w-3 h-3" aria-hidden="true" />
            <span>{isEvaluating ? "Evaluating..." : "Run Evaluation"}</span>
          </button>
        </form>

        {result !== null && (
          <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs">
            <span className="text-emerald-800 font-semibold block mb-0.5">Computed Output:</span>
            <span className="font-mono text-base font-bold text-emerald-950">{result.toFixed(6)}</span>
          </div>
        )}
      </div>

      {/* Topological Percolation Check */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-purple-600" aria-hidden="true" />
          <h3 className="text-sm font-bold text-slate-900">Topological Percolation Check</h3>
        </div>
        <p className="text-xs text-slate-500">
          Evaluates phase transition and giant component connectivity across the document knowledge graph.
        </p>

        <button
          type="button"
          onClick={handleCheckTopology}
          disabled={isLoadingTopology}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-medium cursor-pointer shadow-xs disabled:opacity-50"
        >
          <Network className="w-3.5 h-3.5" aria-hidden="true" />
          <span>{isLoadingTopology ? "Analyzing..." : "Analyze Topology"}</span>
        </button>

        {topology && (
          <div className="p-3 rounded-lg bg-purple-50 border border-purple-200 text-xs space-y-2">
            <div className="flex items-center justify-between font-semibold text-purple-900">
              <span>Percolation State:</span>
              <span className="flex items-center gap-1 text-emerald-700 font-bold">
                <CheckCircle className="w-3.5 h-3.5" aria-hidden="true" />
                {topology.isPercolated ? "Supercritical (Connected)" : "Subcritical"}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px] text-purple-800 font-mono">
              <div>Nodes: {topology.numNodes}</div>
              <div>Edges: {topology.numEdges}</div>
              <div>Threshold p_c: {topology.percolationThreshold}</div>
              <div>Giant Comp: {(topology.giantComponentFraction * 100).toFixed(1)}%</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
