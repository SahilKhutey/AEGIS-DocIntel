"use client";

import React, { useState, useMemo } from "react";
import type { KnowledgeNode, KnowledgeEdge } from "../types";
import { ZoomIn, ZoomOut, RotateCcw, List, Network } from "lucide-react";

type Props = {
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
  onOpenDocument?: (documentId: string) => void;
};

export function KnowledgeGraph({ nodes, edges, onOpenDocument }: Props) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string>("all");
  const [viewMode, setViewMode] = useState<"visual" | "table">("visual");
  const [zoomLevel, setZoomLevel] = useState(1);

  // Filter nodes by selected type
  const filteredNodes = useMemo(() => {
    if (selectedType === "all") return nodes;
    return nodes.filter((n) => n.type.toLowerCase() === selectedType.toLowerCase());
  }, [nodes, selectedType]);

  const activeNodeIds = useMemo(
    () => new Set(filteredNodes.map((n) => n.id)),
    [filteredNodes],
  );

  // Filter edges connected to active nodes
  const filteredEdges = useMemo(() => {
    return edges.filter(
      (e) => activeNodeIds.has(e.source) && activeNodeIds.has(e.target),
    );
  }, [edges, activeNodeIds]);

  // Unique node types
  const nodeTypes = useMemo(() => {
    const types = new Set(nodes.map((n) => n.type));
    return ["all", ...Array.from(types)];
  }, [nodes]);

  // Compute node positions on visual SVG canvas (circular layout)
  const nodePositions = useMemo(() => {
    const count = filteredNodes.length;
    const positions = new Map<string, { x: number; y: number }>();
    if (count === 0) return positions;

    const centerX = 350;
    const centerY = 240;
    const radius = Math.min(centerX - 80, centerY - 40, 40 + count * 22);

    filteredNodes.forEach((node, idx) => {
      const angle = (2 * Math.PI * idx) / count;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      positions.set(node.id, { x, y });
    });

    return positions;
  }, [filteredNodes]);

  const selectedNode = useMemo(
    () => nodes.find((n) => n.id === selectedNodeId) || null,
    [nodes, selectedNodeId],
  );

  const selectedNodeEdges = useMemo(() => {
    if (!selectedNodeId) return [];
    return edges.filter(
      (e) => e.source === selectedNodeId || e.target === selectedNodeId,
    );
  }, [edges, selectedNodeId]);

  return (
    <div className="space-y-4">
      {/* Controls & Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-gray-200 shadow-xs">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-xs font-semibold uppercase text-gray-500 mr-2">
            Filter Type:
          </span>
          {nodeTypes.map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setSelectedType(type)}
              className={`rounded-lg px-2.5 py-1 text-xs font-medium capitalize border transition ${
                selectedType === type
                  ? "bg-blue-600 text-white border-blue-600 shadow-xs"
                  : "bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100"
              }`}
            >
              {type}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          {/* View mode toggle */}
          <div className="flex items-center rounded-xl border border-gray-200 bg-gray-50 p-0.5">
            <button
              type="button"
              onClick={() => setViewMode("visual")}
              aria-label="Visual graph view"
              className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                viewMode === "visual"
                  ? "bg-white text-gray-900 shadow-xs"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              <Network className="h-3.5 w-3.5" />
              <span>Canvas</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("table")}
              aria-label="Accessible table view"
              className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
                viewMode === "table"
                  ? "bg-white text-gray-900 shadow-xs"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              <List className="h-3.5 w-3.5" />
              <span>Table</span>
            </button>
          </div>

          {/* Zoom controls (visual mode only) */}
          {viewMode === "visual" && (
            <div className="flex items-center rounded-xl border border-gray-200 bg-gray-50 p-0.5">
              <button
                type="button"
                onClick={() => setZoomLevel((z) => Math.min(z + 0.2, 1.8))}
                aria-label="Zoom in graph"
                className="p-1.5 text-gray-600 hover:text-gray-900"
              >
                <ZoomIn className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setZoomLevel((z) => Math.max(z - 0.2, 0.6))}
                aria-label="Zoom out graph"
                className="p-1.5 text-gray-600 hover:text-gray-900"
              >
                <ZoomOut className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setZoomLevel(1)}
                aria-label="Reset zoom"
                className="p-1.5 text-gray-600 hover:text-gray-900"
              >
                <RotateCcw className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Graph Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* Canvas or Table Area */}
        <div className="lg:col-span-3">
          {viewMode === "visual" ? (
            <div className="relative h-[520px] w-full overflow-hidden rounded-2xl border border-gray-200 bg-gray-50 shadow-inner flex items-center justify-center">
              {filteredNodes.length === 0 ? (
                <p className="text-sm text-gray-400">No graph nodes match current filters.</p>
              ) : (
                <svg
                  viewBox="0 0 700 480"
                  className="w-full h-full cursor-grab"
                  style={{ transform: `scale(${zoomLevel})`, transformOrigin: "center center", transition: "transform 0.15s ease-out" }}
                >
                  <defs>
                    <marker
                      id="arrow"
                      viewBox="0 0 10 10"
                      refX="22"
                      refY="5"
                      markerWidth="6"
                      markerHeight="6"
                      orient="auto-start-reverse"
                    >
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
                    </marker>
                  </defs>

                  {/* Draw Edges */}
                  {filteredEdges.map((edge) => {
                    const srcPos = nodePositions.get(edge.source);
                    const tgtPos = nodePositions.get(edge.target);
                    if (!srcPos || !tgtPos) return null;

                    const midX = (srcPos.x + tgtPos.x) / 2;
                    const midY = (srcPos.y + tgtPos.y) / 2;

                    return (
                      <g key={edge.id} className="transition-opacity">
                        <line
                          x1={srcPos.x}
                          y1={srcPos.y}
                          x2={tgtPos.x}
                          y2={tgtPos.y}
                          stroke="#cbd5e1"
                          strokeWidth="1.5"
                          markerEnd="url(#arrow)"
                        />
                        <text
                          x={midX}
                          y={midY - 4}
                          textAnchor="middle"
                          fill="#64748b"
                          fontSize="9"
                          className="select-none font-medium"
                        >
                          {edge.relationship.length > 20
                            ? `${edge.relationship.slice(0, 18)}...`
                            : edge.relationship}
                        </text>
                      </g>
                    );
                  })}

                  {/* Draw Nodes */}
                  {filteredNodes.map((node) => {
                    const pos = nodePositions.get(node.id);
                    if (!pos) return null;
                    const isSelected = selectedNodeId === node.id;
                    const isDoc = node.type.toLowerCase() === "document";

                    return (
                      <g
                        key={node.id}
                        transform={`translate(${pos.x}, ${pos.y})`}
                        onClick={() => setSelectedNodeId(node.id)}
                        className="cursor-pointer group"
                      >
                        <circle
                          r={isSelected ? 22 : 18}
                          fill={isDoc ? "#dbeafe" : "#fef3c7"}
                          stroke={isSelected ? "#2563eb" : isDoc ? "#3b82f6" : "#d97706"}
                          strokeWidth={isSelected ? 3 : 1.5}
                          className="transition-all"
                        />
                        <text
                          y={30}
                          textAnchor="middle"
                          fill="#1e293b"
                          fontSize="11"
                          fontWeight={isSelected ? "700" : "500"}
                          className="select-none pointer-events-none"
                        >
                          {node.label.length > 16 ? `${node.label.slice(0, 14)}...` : node.label}
                        </text>
                        <text
                          y={41}
                          textAnchor="middle"
                          fill="#64748b"
                          fontSize="9"
                          className="select-none uppercase tracking-wider font-semibold pointer-events-none"
                        >
                          {node.type}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              )}
            </div>
          ) : (
            /* Accessible Table View (WCAG 2.2 AA Alternative) */
            <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-xs">
              <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-700">
                  Accessible Knowledge Graph Table
                </h3>
                <span className="text-xs text-gray-500 font-mono">
                  {filteredNodes.length} nodes · {filteredEdges.length} relationships
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
                  <thead className="bg-gray-50 text-xs font-semibold uppercase text-gray-500">
                    <tr>
                      <th scope="col" className="px-4 py-3">Node Label</th>
                      <th scope="col" className="px-4 py-3">Type</th>
                      <th scope="col" className="px-4 py-3">Identifier</th>
                      <th scope="col" className="px-4 py-3">Connected Relationships</th>
                      <th scope="col" className="px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {filteredNodes.map((n) => {
                      const countEdges = edges.filter(
                        (e) => e.source === n.id || e.target === n.id,
                      ).length;

                      return (
                        <tr
                          key={n.id}
                          className={`hover:bg-gray-50 ${selectedNodeId === n.id ? "bg-blue-50/60" : ""}`}
                        >
                          <td className="px-4 py-3 font-semibold text-gray-900">{n.label}</td>
                          <td className="px-4 py-3">
                            <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium capitalize text-gray-800">
                              {n.type}
                            </span>
                          </td>
                          <td className="px-4 py-3 font-mono text-xs text-gray-500">{n.id}</td>
                          <td className="px-4 py-3 text-xs text-gray-600">{countEdges} relationship(s)</td>
                          <td className="px-4 py-3">
                            <button
                              type="button"
                              onClick={() => setSelectedNodeId(n.id)}
                              className="text-xs font-semibold text-blue-600 hover:text-blue-800"
                            >
                              Inspect
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Selected Node Details Sidebar */}
        <div className="lg:col-span-1 rounded-2xl border border-gray-200 bg-white p-5 shadow-xs space-y-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 pb-2 border-b border-gray-100">
            Node Details
          </h3>

          {selectedNode ? (
            <div className="space-y-3">
              <div>
                <span className="text-xs font-medium text-gray-400 block">Label</span>
                <p className="text-sm font-bold text-gray-900">{selectedNode.label}</p>
              </div>

              <div>
                <span className="text-xs font-medium text-gray-400 block">Type</span>
                <span className="inline-flex items-center rounded-md bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 capitalize">
                  {selectedNode.type}
                </span>
              </div>

              <div>
                <span className="text-xs font-medium text-gray-400 block">ID</span>
                <p className="text-xs font-mono text-gray-600 break-all">{selectedNode.id}</p>
              </div>

              {selectedNode.documentIds && selectedNode.documentIds.length > 0 && (
                <div>
                  <span className="text-xs font-medium text-gray-400 block mb-1">Source Documents</span>
                  <div className="space-y-1">
                    {selectedNode.documentIds.map((docId) => (
                      <button
                        key={docId}
                        type="button"
                        onClick={() => onOpenDocument?.(docId)}
                        className="text-xs font-semibold text-blue-600 hover:underline block truncate max-w-full"
                      >
                        {docId} &rarr;
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="pt-2 border-t border-gray-100">
                <span className="text-xs font-medium text-gray-400 block mb-1">
                  Connected Edges ({selectedNodeEdges.length})
                </span>
                <ul className="space-y-1 text-xs text-gray-700 max-h-36 overflow-y-auto">
                  {selectedNodeEdges.map((e) => (
                    <li key={e.id} className="p-1.5 rounded bg-gray-50 border border-gray-100">
                      <span className="font-semibold text-gray-900">{e.relationship}</span>
                      <p className="text-[11px] text-gray-500">
                        {e.source === selectedNode.id ? `&rarr; ${e.target}` : `&larr; ${e.source}`}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-400 italic">
              Select any node in the graph or table to view detailed relationships and provenance.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
