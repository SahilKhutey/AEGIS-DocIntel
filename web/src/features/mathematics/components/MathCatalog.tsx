"use client";

import React, { useState, useEffect } from "react";
import {
  MOCK_VECTOR_REP,
  MOCK_MATRIX_REP,
  STANDARD_EQUATIONS,
  TRANSFORMATION_HISTORY,
  getRepresentations,
} from "../api/mathematics.api";
import { VectorRepresentation, MatrixRepresentation } from "../types";
import { VectorViewer } from "./VectorViewer";
import { MatrixViewer } from "./MatrixViewer";
import { EquationRenderer } from "./EquationRenderer";
import { TransformationTrace } from "./TransformationTrace";
import { ProvenanceViewer } from "./ProvenanceViewer";
import { InteractiveMathPlayground } from "./InteractiveMathPlayground";
import { Binary, BookOpen, Layers, Terminal } from "lucide-react";

export type MathTab = "representations" | "equations" | "transformations" | "evaluator";

export const MathCatalog: React.FC = () => {
  const [activeTab, setActiveTab] = useState<MathTab>("representations");
  const [vectorRep, setVectorRep] = useState<VectorRepresentation>(MOCK_VECTOR_REP);
  const [matrixRep, setMatrixRep] = useState<MatrixRepresentation>(MOCK_MATRIX_REP);

  useEffect(() => {
    let mounted = true;
    getRepresentations()
      .then((reps) => {
        if (!mounted) return;
        const v = reps.find((r): r is VectorRepresentation => r.type === "vector");
        const m = reps.find((r): r is MatrixRepresentation => r.type === "matrix");
        if (v) setVectorRep(v);
        if (m) setMatrixRep(m);
      })
      .catch(() => {
        // Fallback already in place
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Mathematical Representations & Formulations</h2>
          <p className="text-xs text-slate-500">
            Explore high-dimensional vector embeddings, kernel matrices, similarity equations, and derivation traces.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md border border-slate-200">
            Precision: float32 / float64
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6" aria-label="Mathematics Sections">
          <button
            type="button"
            onClick={() => setActiveTab("representations")}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "representations"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
          >
            <Binary className="w-4 h-4" aria-hidden="true" />
            <span>Vectors & Matrices</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("equations")}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "equations"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
          >
            <BookOpen className="w-4 h-4" aria-hidden="true" />
            <span>Formulas & Equations</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("transformations")}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "transformations"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
          >
            <Layers className="w-4 h-4" aria-hidden="true" />
            <span>Transformation Trace</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("evaluator")}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "evaluator"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300"
            }`}
          >
            <Terminal className="w-4 h-4" aria-hidden="true" />
            <span>Unified Evaluator</span>
          </button>
        </nav>
      </div>

      {/* Tab Panels */}
      {activeTab === "representations" && (
        <div className="space-y-6">
          <div className="space-y-6">
            <VectorViewer vector={vectorRep} />
            <ProvenanceViewer provenance={vectorRep.provenance} />
          </div>

          <div className="space-y-6 pt-4 border-t border-slate-200">
            <MatrixViewer matrix={matrixRep} />
            <ProvenanceViewer provenance={matrixRep.provenance} />
          </div>
        </div>
      )}

      {activeTab === "equations" && (
        <div className="grid grid-cols-1 gap-6">
          {STANDARD_EQUATIONS.map((eq) => (
            <EquationRenderer key={eq.id} equation={eq} />
          ))}
        </div>
      )}

      {activeTab === "transformations" && (
        <TransformationTrace steps={TRANSFORMATION_HISTORY} />
      )}

      {activeTab === "evaluator" && (
        <InteractiveMathPlayground />
      )}
    </div>
  );
};
