"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { DocumentListSchema, type DocumentItem } from "@/lib/schemas";
import { apiRequest } from "@/lib/api-client";
import {
  MessageSquare,
  Search,
  FileSearch,
  Network,
  GitCompare,
  ArrowRight,
  ShieldCheck,
  FileText,
  Sparkles,
} from "lucide-react";

export default function IntelligenceHubPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        setLoading(true);
        const data = await apiRequest("/api/v1/documents", DocumentListSchema);
        setDocuments(data.items || []);
      } catch {
        // Continue even if documents fail
      } finally {
        setLoading(false);
      }
    }
    void loadStats();
  }, []);

  const capabilities = [
    {
      title: "Ask AEGIS",
      description: "Natural-language questions over authorized documents with grounded citations, claim traceability, and safe abstention.",
      href: "/ask",
      icon: MessageSquare,
      badge: "Grounded Q&A",
      actionText: "Open Ask AEGIS",
    },
    {
      title: "Document Retrieval",
      description: "Search document passages, inspect hybrid BM25 and vector relevance scores, and trace ranking metadata.",
      href: "/intelligence/retrieval",
      icon: Search,
      badge: "Hybrid Search",
      actionText: "Explore Retrieval",
    },
    {
      title: "Evidence Explorer",
      description: "Trace answer claims to verbatim source passages, page references, and ground truth document coordinates.",
      href: "/intelligence/evidence",
      icon: FileSearch,
      badge: "Traceability",
      actionText: "Inspect Evidence",
    },
    {
      title: "Knowledge Visualization",
      description: "Visualize extracted entities, concepts, and cross-document relationships with an accessible structured table view.",
      href: "/intelligence/knowledge",
      icon: Network,
      badge: "Entity Graph",
      actionText: "View Knowledge Graph",
    },
    {
      title: "Compare Documents",
      description: "Align multi-document agreements, detect quantity/date discrepancies, and inspect conflicting evidence across versions.",
      href: "/compare",
      icon: GitCompare,
      badge: "Cross-Document",
      actionText: "Start Comparison",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Document Intelligence Workspace
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Grounded question answering, hybrid passage retrieval, verbatim evidence provenance, knowledge graph, and cross-document comparison.
        </p>
      </div>

      {/* Intelligence Operational State Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs flex items-center gap-4">
          <div className="rounded-xl bg-blue-50 p-3 text-blue-600">
            <FileText className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
              Authorized Scope
            </span>
            <p className="text-xl font-bold text-gray-900">
              {loading ? "..." : `${documents.length} Documents`}
            </p>
            <p className="text-xs text-gray-500">Tenant repository indexed</p>
          </div>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs flex items-center gap-4">
          <div className="rounded-xl bg-emerald-50 p-3 text-emerald-600">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
              Evidence Integrity
            </span>
            <p className="text-xl font-bold text-emerald-700">Strict Grounding</p>
            <p className="text-xs text-gray-500">Zero unverified citations</p>
          </div>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs flex items-center gap-4">
          <div className="rounded-xl bg-purple-50 p-3 text-purple-600">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
              Intelligence Mode
            </span>
            <p className="text-xl font-bold text-purple-900">Multi-Capability</p>
            <p className="text-xs text-gray-500">RAG · KG · Cross-Compare</p>
          </div>
        </div>
      </div>

      {/* Capability Cards */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-700">
          Intelligence Capabilities
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {capabilities.map((cap) => {
            const Icon = cap.icon;
            return (
              <div
                key={cap.title}
                className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xs flex flex-col justify-between hover:border-blue-400 hover:shadow-sm transition"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="rounded-xl bg-blue-50 p-2.5 text-blue-600">
                      <Icon className="h-5 w-5" />
                    </div>
                    <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700">
                      {cap.badge}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-gray-900">{cap.title}</h3>
                  <p className="text-xs text-gray-600 leading-relaxed">{cap.description}</p>
                </div>

                <div className="pt-5 mt-4 border-t border-gray-100">
                  <Link
                    href={cap.href}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800 group"
                  >
                    <span>{cap.actionText}</span>
                    <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
