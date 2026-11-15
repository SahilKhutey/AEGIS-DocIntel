"use client";

import React, { useState } from "react";
import type { MatrixRepresentation } from "../types";

export interface MatrixViewerProps {
  matrix: MatrixRepresentation;
}

export const MatrixViewer: React.FC<MatrixViewerProps> = ({ matrix }) => {
  const [selectedCell, setSelectedCell] = useState<{
    row: number;
    col: number;
    val: number;
  } | null>(null);

  // Value color interpolation: 0.0 -> white/light slate, 1.0 -> deep blue
  const getCellBg = (val: number) => {
    const clamped = Math.max(0, Math.min(1, val));
    if (clamped >= 0.9) return "bg-blue-700 text-white font-bold";
    if (clamped >= 0.7) return "bg-blue-600 text-white font-medium";
    if (clamped >= 0.4) return "bg-blue-200 text-slate-900 font-medium";
    if (clamped >= 0.2) return "bg-blue-100 text-slate-900";
    if (clamped > 0) return "bg-blue-50 text-slate-800";
    return "bg-slate-50 text-slate-700";
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-bold text-slate-900">{matrix.name}</h3>
          <p className="text-xs text-slate-500">
            {matrix.rows} × {matrix.cols} matrix · Sparsity: {matrix.sparsity}%
            {matrix.conditionNumber && ` · Condition No: ${matrix.conditionNumber.toFixed(2)}`}
          </p>
        </div>

        {selectedCell ? (
          <div className="text-xs bg-blue-50 border border-blue-200 text-blue-900 px-3 py-1.5 rounded-lg flex items-center gap-2">
            <span className="font-semibold">Selected:</span>
            <span>
              Row {selectedCell.row} ({matrix.rowLabels?.[selectedCell.row] || `R${selectedCell.row}`}),
              Col {selectedCell.col} ({matrix.colLabels?.[selectedCell.col] || `C${selectedCell.col}`})
            </span>
            <span className="font-mono font-bold bg-white px-2 py-0.5 rounded border border-blue-200">
              {selectedCell.val.toFixed(4)}
            </span>
          </div>
        ) : (
          <div className="text-xs text-slate-600 italic">Click any cell to inspect value</div>
        )}
      </div>

      {/* Matrix Grid */}
      <div className="overflow-x-auto pb-2">
        <div className="inline-block min-w-full">
          <table className="border-collapse text-xs">
            <thead>
              <tr>
                <th className="p-2 text-slate-600 font-mono text-[10px]">#</th>
                {matrix.colLabels?.map((label, cIdx) => (
                  <th
                    key={cIdx}
                    className="p-2 text-center text-slate-600 font-medium text-[10px] min-w-[50px] whitespace-nowrap"
                  >
                    {label}
                  </th>
                )) ||
                  Array.from({ length: matrix.cols }, (_, cIdx) => (
                    <th key={cIdx} className="p-2 text-center text-slate-600 font-mono text-[10px]">
                      C{cIdx}
                    </th>
                  ))}
              </tr>
            </thead>
            <tbody>
              {matrix.matrix.map((rowVals, rIdx) => (
                <tr key={rIdx}>
                  <td className="p-2 text-slate-600 font-medium text-[10px] whitespace-nowrap">
                    {matrix.rowLabels?.[rIdx] || `R${rIdx}`}
                  </td>
                  {rowVals.map((val, cIdx) => {
                    const isDiagonal = rIdx === cIdx;
                    const isSelected = selectedCell?.row === rIdx && selectedCell?.col === cIdx;
                    return (
                      <td
                        key={cIdx}
                        onClick={() => setSelectedCell({ row: rIdx, col: cIdx, val })}
                        className={`p-2.5 text-center font-mono cursor-pointer transition-all border border-slate-100 ${getCellBg(
                          val,
                        )} ${isDiagonal ? "ring-1 ring-blue-700 font-bold" : ""} ${
                          isSelected ? "ring-2 ring-black scale-105 z-10" : "hover:opacity-80"
                        }`}
                        title={`[${rIdx}, ${cIdx}] = ${val}`}
                      >
                        {val.toFixed(2)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-between text-xs text-slate-500 pt-3 border-t border-slate-100">
        <span>Symmetric Gram Kernel (Cosine Distance)</span>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px]">0.0 (Orthogonal)</span>
          <span className="w-4 h-3 rounded bg-blue-50 inline-block border border-slate-200" />
          <span className="w-4 h-3 rounded bg-blue-200 inline-block" />
          <span className="w-4 h-3 rounded bg-blue-400 inline-block" />
          <span className="w-4 h-3 rounded bg-blue-600 inline-block" />
          <span className="text-[10px]">1.0 (Collinear)</span>
        </div>
      </div>
    </div>
  );
};
