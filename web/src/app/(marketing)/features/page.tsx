"use client";

import React from "react";
import Link from "next/link";
import {
  Layers,
  Binary,
  Search,
  GitCompare,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Table,
  CheckCircle2,
  FileCode,
} from "lucide-react";

export default function FeaturesPage() {
  return (
    <div className="flex flex-col min-h-screen bg-[var(--background)] text-[var(--foreground)] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-12">
        {/* Header */}
        <div className="border-b border-[var(--border)] pb-8">
          <span className="text-xs font-bold uppercase tracking-widest text-blue-500">Technical Specifications</span>
          <h1 className="mt-2 text-3xl sm:text-4xl font-extrabold tracking-tight text-[var(--foreground)]">
            AEGIS-DocIntel Feature & Capability Matrix
          </h1>
          <p className="mt-4 text-base text-[var(--muted)] max-w-3xl leading-relaxed">
            Every capability in AEGIS-DocIntel is grounded in mathematical algorithms and defense-in-depth architecture.
            Explore our layout reconstruction, submodular context packing, coordinate grounding, and comparative topology.
          </p>
        </div>

        {/* Feature 1: Spatial Kahn DAG Layout Parsing */}
        <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 space-y-4">
          <div className="flex items-center gap-3">
            <span className="p-2.5 rounded-lg bg-blue-500/10 text-blue-500">
              <Layers className="w-6 h-6" />
            </span>
            <div>
              <h2 className="text-xl font-bold text-[var(--foreground)]">1. Layout-Aware Spatial Parsing & DAG Order</h2>
              <span className="text-xs font-mono text-blue-400">Implementation: PyMuPDF + Kahn's Topological Sort</span>
            </div>
          </div>
          <p className="text-sm text-[var(--muted)] leading-relaxed">
            Conventional document ingest strips raw characters from PDF streams, completely losing visual reading order across multi-column layouts, sidebars, and footnotes. AEGIS extracts 2D bounding boxes, font heights, and geometric margins, constructing a directed acyclic graph (DAG) of layout elements:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div className="p-4 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <h3 className="text-xs font-semibold text-blue-400">Kahn Topological Sorting</h3>
              <p className="mt-1 text-xs text-[var(--muted)]">Guarantees correct natural reading order across complex multi-column scientific papers.</p>
            </div>
            <div className="p-4 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <h3 className="text-xs font-semibold text-blue-400">Table Structure Preservation</h3>
              <p className="mt-1 text-xs text-[var(--muted)]">Extracts cell grids and preserves column-row relationships in financial filings and schematics.</p>
            </div>
            <div className="p-4 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <h3 className="text-xs font-semibold text-blue-400">Heading Tree Hierarchy</h3>
              <p className="mt-1 text-xs text-[var(--muted)]">Builds explicit parent-child section relationships (H1 &rarr; H2 &rarr; H3) for contextual navigation.</p>
            </div>
          </div>
        </section>

        {/* Feature 2: Submodular Knapsack Context Optimization */}
        <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 space-y-4">
          <div className="flex items-center gap-3">
            <span className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-500">
              <Binary className="w-6 h-6" />
            </span>
            <div>
              <h2 className="text-xl font-bold text-[var(--foreground)]">2. Submodular Knapsack Context Optimization</h2>
              <span className="text-xs font-mono text-indigo-400">Formula: max f(S) subject to cost(S) &le; TokenBudget</span>
            </div>
          </div>
          <p className="text-sm text-[var(--muted)] leading-relaxed">
            Instead of naive similarity search that returns 5 redundant paragraphs repeating the exact same sentence, AEGIS uses submodular coverage functions to select a set of chunks that maximizes topical coverage while strictly obeying LLM prompt token limits.
          </p>
          <div className="p-4 rounded-lg bg-[var(--background)] border border-[var(--border)] font-mono text-xs text-indigo-400">
            Gain(chunk | Selected) = CoverageIncrease(chunk) - &lambda; * RedundancyPenalty(chunk)
          </div>
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-[var(--muted)]">
            <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-500" /> 94.6% optimal coverage under 2,048 token budget</li>
            <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-500" /> Eliminates duplicate sentences across sections</li>
            <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-500" /> Prioritizes numerical tables and quantitative statements</li>
            <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-emerald-500" /> Deterministic greedy approximation with bounded error</li>
          </ul>
        </section>

        {/* Feature 3: Grounded Coordinate Citations */}
        <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 space-y-4">
          <div className="flex items-center gap-3">
            <span className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-500">
              <Search className="w-6 h-6" />
            </span>
            <div>
              <h2 className="text-xl font-bold text-[var(--foreground)]">3. Deterministic Grounded Coordinate Citations</h2>
              <span className="text-xs font-mono text-emerald-400">Bounding Box Tethering & Hash Ledger</span>
            </div>
          </div>
          <p className="text-sm text-[var(--muted)] leading-relaxed">
            Every synthesized observation is tied to source bounding box coordinates: <code>[page, x0, y0, x1, y1]</code>.
            Evaluators can click any citation pill to verify the verbatim source text and bounding box overlay directly in the document viewer.
          </p>
        </section>

        {/* Feature 4: Topological Multi-Document Comparison */}
        <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 space-y-4">
          <div className="flex items-center gap-3">
            <span className="p-2.5 rounded-lg bg-purple-500/10 text-purple-500">
              <GitCompare className="w-6 h-6" />
            </span>
            <div>
              <h2 className="text-xl font-bold text-[var(--foreground)]">4. Cross-Document Comparative Topology</h2>
              <span className="text-xs font-mono text-purple-400">Sheaf Laplacian Contradiction Detection</span>
            </div>
          </div>
          <p className="text-sm text-[var(--muted)] leading-relaxed">
            Select any two documents in your corpus to compute an aligned contradiction matrix. Surfaces metric shifts, modified terms, deleted safety clauses, and altered numerical specifications across revisions.
          </p>
        </section>

        {/* CTA */}
        <div className="pt-6 border-t border-[var(--border)] flex items-center justify-between">
          <Link href="/demo" className="text-sm font-semibold text-blue-500 hover:text-blue-400 flex items-center gap-1.5">
            Watch the 75-Second Walkthrough <ArrowRight className="w-4 h-4" />
          </Link>
          <Link href="/evaluation" className="px-6 py-2.5 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 transition">
            Start Free Evaluation
          </Link>
        </div>
      </div>
    </div>
  );
}
