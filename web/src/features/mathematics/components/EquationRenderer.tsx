import React from "react";
import type { EquationDefinition } from "../types";
import { BookOpen, Hash } from "lucide-react";

export interface EquationRendererProps {
  equation: EquationDefinition;
}

export const EquationRenderer: React.FC<EquationRendererProps> = ({ equation }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-blue-600" aria-hidden="true" />
          <h3 className="text-sm font-bold text-slate-900">{equation.name}</h3>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-slate-100 text-slate-600">
          {equation.category}
        </span>
      </div>

      <p className="text-xs text-slate-600">{equation.description}</p>

      {/* LaTeX Formula Display Box */}
      <div className="p-4 rounded-lg bg-slate-900 text-slate-100 font-mono text-xs overflow-x-auto border border-slate-800">
        <div className="text-[10px] uppercase text-slate-600 font-sans font-semibold mb-1">
          Mathematical Formulation (LaTeX)
        </div>
        <code className="text-emerald-300 font-bold tracking-wide select-all">
          {equation.latex}
        </code>
      </div>

      {/* Variable Descriptions */}
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1">
          <Hash className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Variables & Notation</span>
        </h4>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
          {equation.variables.map((v) => (
            <div
              key={v.symbol}
              className="p-2.5 rounded-lg bg-slate-50 border border-slate-100"
            >
              <dt className="font-mono font-bold text-slate-800 mb-0.5">
                {v.symbol} — <span className="font-sans font-semibold text-slate-700">{v.name}</span>
              </dt>
              <dd className="text-slate-500 text-[11px] leading-relaxed">
                {v.description}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
};
