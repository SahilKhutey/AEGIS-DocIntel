import React from "react";
import type { TransformationStep } from "../types";
import { Cpu, Clock, Layers } from "lucide-react";

export interface TransformationTraceProps {
  steps: TransformationStep[];
}

export const TransformationTrace: React.FC<TransformationTraceProps> = ({ steps }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex items-center gap-2">
        <Layers className="w-4 h-4 text-purple-600" aria-hidden="true" />
        <h3 className="text-sm font-bold text-slate-900">Transformation Pipeline Trace</h3>
      </div>

      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
        {steps.map((step) => (
          <div key={step.stepNumber} className="relative group">
            {/* Step marker dot */}
            <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold shadow-xs">
              {step.stepNumber}
            </div>

            <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50 hover:bg-white transition-colors">
              <div className="flex items-center justify-between gap-2 mb-1">
                <h4 className="text-xs font-bold text-slate-900">{step.name}</h4>
                <span className="flex items-center gap-1 text-[11px] text-slate-400 font-mono">
                  <Clock className="w-3 h-3" aria-hidden="true" />
                  {step.durationMs}ms
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs my-2 font-mono text-[11px]">
                <div className="bg-white p-2 rounded border border-slate-100">
                  <span className="text-slate-400 block text-[10px] font-sans font-medium uppercase">Input</span>
                  <span className="text-slate-700 font-semibold">{step.inputShape}</span>
                </div>
                <div className="bg-white p-2 rounded border border-slate-100">
                  <span className="text-slate-400 block text-[10px] font-sans font-medium uppercase">Output</span>
                  <span className="text-blue-700 font-semibold">{step.outputShape}</span>
                </div>
              </div>

              <div className="text-[11px] text-slate-500 font-mono flex items-center gap-1">
                <Cpu className="w-3 h-3 text-slate-400 shrink-0" aria-hidden="true" />
                <span>{step.operation}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
