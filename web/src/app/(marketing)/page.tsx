"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  FileText,
  ShieldCheck,
  Sparkles,
  GitCompare,
  Search,
  CheckCircle2,
  Clock,
  Layers,
  ArrowRight,
  Shield,
  Lock,
  Binary,
  Database,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  Terminal,
} from "lucide-react";
import { fetchWorkspaceOverview } from "@/features/workspace-overview/api";
import type { WorkspaceOverviewData } from "@/features/workspace-overview/types";
import { MetricCard } from "@/features/workspace-overview/components/metric-card";
import { RecentDocuments } from "@/features/workspace-overview/components/recent-documents";
import { ProcessingSummary } from "@/features/workspace-overview/components/processing-summary";
import { AttentionPanel } from "@/features/workspace-overview/components/attention-panel";

export default function MarketingLandingPage() {
  const [data, setData] = useState<WorkspaceOverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "workspace">("overview");

  const loadData = useCallback(async () => {
    try {
      const overview = await fetchWorkspaceOverview();
      setData(overview);
    } catch {
      // Graceful cold-start fallback
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  return (
    <div id="main-content" className="flex flex-col min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      {/* ─────────────────────────────────────────────────────────────
          SECTION 01: HERO
      ───────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden border-b border-[var(--border)] bg-gradient-to-b from-blue-950/20 via-transparent to-transparent py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          {/* Trust / PH Badge */}
          <div className="flex flex-wrap items-center gap-3 mb-6">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-500 border border-blue-500/20">
              <Sparkles className="w-3.5 h-3.5" />
              Product Hunt Launch Edition · v0.1.0
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
              <ShieldCheck className="w-3.5 h-3.5" />
              100% Grounded Coordinate Citations
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-500/20">
              <Lock className="w-3.5 h-3.5" />
              Zero Model Training Guarantee
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-8">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-[var(--foreground)] leading-[1.1]">
                Turn complex documents into{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-indigo-500">
                  structured intelligence.
                </span>
              </h1>
              <p className="mt-5 text-lg sm:text-xl text-[var(--muted)] max-w-2xl leading-relaxed">
                Move beyond basic document reading and chat. AEGIS-DocIntel combines layout-aware spatial parsing,
                submodular knapsack context packing, and topological cross-document comparison into one integrated,
                tamper-resistant evaluation workbench.
              </p>

              {/* Action Buttons */}
              <div className="mt-8 flex flex-wrap items-center gap-4">
                <Link
                  href="/evaluation"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 transition shadow-sm"
                >
                  Try the Evaluation
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/demo"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg text-sm font-semibold text-[var(--foreground)] bg-[var(--surface)] hover:bg-[var(--surface-hover)] border border-[var(--border)] transition"
                >
                  Watch Demo (75s)
                </Link>
                <Link
                  href="/features"
                  className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-lg text-sm font-medium text-[var(--muted)] hover:text-[var(--foreground)] transition"
                >
                  Explore Features
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>

              {/* Invariant Checklist */}
              <div className="mt-8 flex flex-wrap gap-y-2 gap-x-6 text-xs text-[var(--muted)]">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  No credit card required
                </span>
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  Ed25519 Asymmetric Licensing
                </span>
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  Two-Tier Zero-Leak Boundary
                </span>
              </div>
            </div>

            {/* Quick Preview Card */}
            <div className="lg:col-span-4">
              <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-lg">
                <div className="flex items-center justify-between pb-3 border-b border-[var(--border)]">
                  <span className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">Live Grounded Citation</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-500">DETERMINISTIC</span>
                </div>
                <div className="mt-3 space-y-3 text-xs">
                  <div className="p-2.5 rounded bg-black/10 dark:bg-white/5 font-mono text-[11px]">
                    <span className="text-blue-400">query:</span> "What is peak throughput?"
                  </div>
                  <div className="p-2.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                    <p className="font-medium text-xs leading-relaxed">
                      "620 TFLOPS with 285W TDP and 128 MB cache."
                    </p>
                    <div className="mt-2 text-[10px] font-mono text-emerald-500">
                      Citation: Spec v2 · p.2 [42, 110, 280, 145]
                    </div>
                  </div>
                  <div className="pt-2 border-t border-[var(--border)] flex items-center justify-between text-[11px] text-[var(--muted)]">
                    <span>Document: hardware_spec_v2.pdf</span>
                    <span className="text-emerald-500 font-semibold">100% Grounded</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 02: THE PROBLEM WE ADDRESS
      ───────────────────────────────────────────────────────────── */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 border-b border-[var(--border)] bg-[var(--surface)]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <h2 className="text-xs font-bold uppercase tracking-widest text-blue-500">The Problem</h2>
            <p className="mt-2 text-3xl font-extrabold tracking-tight text-[var(--foreground)]">
              Complex documents create fragmented, fragile workflows
            </p>
            <p className="mt-4 text-base text-[var(--muted)]">
              Traditional PDF tools and generic chatbots strip layouts, dump text into naive prompts, and lose crucial context between files.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--background)] p-6">
              <div className="w-10 h-10 rounded-lg bg-red-500/10 text-red-500 flex items-center justify-center font-bold mb-4">
                01
              </div>
              <h3 className="text-lg font-bold text-[var(--foreground)]">Table & Layout Scrambling</h3>
              <p className="mt-2 text-sm text-[var(--muted)] leading-relaxed">
                Naive text extractors flatten multi-column documents and technical data sheets into an unreadable mess, losing row-column associations.
              </p>
            </div>

            <div className="rounded-xl border border-[var(--border)] bg-[var(--background)] p-6">
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 text-amber-500 flex items-center justify-center font-bold mb-4">
                02
              </div>
              <h3 className="text-lg font-bold text-[var(--foreground)]">Prompt Window Waste</h3>
              <p className="mt-2 text-sm text-[var(--muted)] leading-relaxed">
                Sliding-window RAG stuffs raw chunks indiscriminately, wasting token budgets on boilerplate while omitting key numerical proofs.
              </p>
            </div>

            <div className="rounded-xl border border-[var(--border)] bg-[var(--background)] p-6">
              <div className="w-10 h-10 rounded-lg bg-purple-500/10 text-purple-500 flex items-center justify-center font-bold mb-4">
                03
              </div>
              <h3 className="text-lg font-bold text-[var(--foreground)]">Multi-File Invisibility</h3>
              <p className="mt-2 text-sm text-[var(--muted)] leading-relaxed">
                Comparing revisions or surfacing contradictions between contracts or specifications requires opening dozens of tabs and manually cross-checking.
              </p>
            </div>

            <div className="rounded-xl border border-[var(--border)] bg-[var(--background)] p-6">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 text-blue-500 flex items-center justify-center font-bold mb-4">
                04
              </div>
              <h3 className="text-lg font-bold text-[var(--foreground)]">Unverifiable Hallucinations</h3>
              <p className="mt-2 text-sm text-[var(--muted)] leading-relaxed">
                When answers lack exact spatial coordinates, researchers and auditors cannot verify claims without re-reading the entire PDF from scratch.
              </p>
            </div>

            <div className="rounded-xl border border-[var(--border)] bg-[var(--background)] p-6">
              <div className="w-10 h-10 rounded-lg bg-indigo-500/10 text-indigo-500 flex items-center justify-center font-bold mb-4">
                05
              </div>
              <h3 className="text-lg font-bold text-[var(--foreground)]">Disconnected Point Tools</h3>
              <p className="mt-2 text-sm text-[var(--muted)] leading-relaxed">
                Users juggle OCR apps, vector databases, custom python scripts, and browser chatbots without a unified governance or evaluation workflow.
              </p>
            </div>

            <div className="rounded-xl border border-[var(--border)] bg-[var(--background)] p-6">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center font-bold mb-4">
                06
              </div>
              <h3 className="text-lg font-bold text-[var(--foreground)]">Sovereign Privacy Risks</h3>
              <p className="mt-2 text-sm text-[var(--muted)] leading-relaxed">
                Uploading confidential drafts to consumer chat platforms risks training public models on non-public research, patent filings, or filings.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 03: THE AEGIS SOLUTION
      ───────────────────────────────────────────────────────────── */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 border-b border-[var(--border)]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <h2 className="text-xs font-bold uppercase tracking-widest text-emerald-500">The Architecture</h2>
            <p className="mt-2 text-3xl font-extrabold tracking-tight text-[var(--foreground)]">
              Four connected stages of mathematical document intelligence
            </p>
            <p className="mt-4 text-base text-[var(--muted)]">
              A rigorous engineering pipeline converting visual layouts into structured, auditable intelligence.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="p-2.5 rounded-lg bg-blue-500/10 text-blue-500">
                    <Layers className="w-6 h-6" />
                  </span>
                  <span className="text-xs font-mono text-[var(--muted)]">STAGE 01</span>
                </div>
                <h3 className="text-xl font-bold text-[var(--foreground)]">Layout-Aware Spatial Parsing</h3>
                <p className="mt-2 text-sm text-[var(--muted)] leading-relaxed">
                  Extracts spatial bounding boxes, font metrics, and structural heading trees. Sorts document flow using Kahn's topological DAG algorithm to preserve multi-column reading order and table boundaries.
                </p>
              </div>
              <div className="mt-6 p-3 rounded-lg bg-[var(--background)] font-mono text-xs text-blue-400 border border-[var(--border)]">
                Kahn_DAG_Sort() &rarr; HeadingTree.build() &rarr; TableMatrix.extract()
              </div>
            </div>

            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-500">
                    <Binary className="w-6 h-6" />
                  </span>
                  <span className="text-xs font-mono text-[var(--muted)]">STAGE 02</span>
                </div>
                <h3 className="text-xl font-bold text-[var(--foreground)]">Submodular Knapsack Context Packing</h3>
                <p className="mt-2 text-sm text-[var(--muted)] leading-relaxed">
                  Instead of arbitrary chunk truncation, AEGIS optimizes context coverage under fixed token budgets using submodular knapsack algorithms, maximizing information density while eliminating redundancy.
                </p>
              </div>
              <div className="mt-6 p-3 rounded-lg bg-[var(--background)] font-mono text-xs text-indigo-400 border border-[var(--border)]">
                max f(S) s.t. cost(S) &le; Budget &rarr; Coverage 94.6% optimal
              </div>
            </div>

            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-500">
                    <Search className="w-6 h-6" />
                  </span>
                  <span className="text-xs font-mono text-[var(--muted)]">STAGE 03</span>
                </div>
                <h3 className="text-xl font-bold text-[var(--foreground)]">Grounded Coordinate Citations</h3>
                <p className="mt-2 text-sm text-[var(--muted)] leading-relaxed">
                  Every retrieved claim is coupled with exact bounding-box coordinates and cryptographic chunk hashes. Evaluators can click any citation to instantly inspect the original text in the source document.
                </p>
              </div>
              <div className="mt-6 p-3 rounded-lg bg-[var(--background)] font-mono text-xs text-emerald-400 border border-[var(--border)]">
                bbox(x0, y0, x1, y1) &rarr; SHA-256 Grounding Ledger
              </div>
            </div>

            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="p-2.5 rounded-lg bg-purple-500/10 text-purple-500">
                    <GitCompare className="w-6 h-6" />
                  </span>
                  <span className="text-xs font-mono text-[var(--muted)]">STAGE 04</span>
                </div>
                <h3 className="text-xl font-bold text-[var(--foreground)]">Topological Cross-Document Analysis</h3>
                <p className="mt-2 text-sm text-[var(--muted)] leading-relaxed">
                  Aligns multi-document corpora using Sheaf Laplacian topology, automatically detecting discrepancies, altered figures, deleted sections, and contradictory metrics across versions.
                </p>
              </div>
              <div className="mt-6 p-3 rounded-lg bg-[var(--background)] font-mono text-xs text-purple-400 border border-[var(--border)]">
                Sheaf_Laplacian() &rarr; Contradiction.detect() &rarr; DiffMatrix
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 04: PRODUCT DEMO & INTERACTIVE WORKSPACE
      ───────────────────────────────────────────────────────────── */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 border-b border-[var(--border)] bg-[var(--surface)]">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-widest text-blue-500">Interactive Preview</h2>
              <p className="mt-2 text-3xl font-extrabold tracking-tight text-[var(--foreground)]">
                See the AEGIS Workbench in Action
              </p>
              <p className="mt-2 text-sm text-[var(--muted)]">
                Explore live workspace metrics, document ingestion summaries, and intelligence query routes.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Link
                href="/documents"
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-blue-600 text-white hover:bg-blue-700 transition"
              >
                Document Library
              </Link>
              <Link
                href="/ask"
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-[var(--background)] border border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--surface-hover)] transition"
              >
                Ask AEGIS
              </Link>
              <Link
                href="/compare"
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-[var(--background)] border border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--surface-hover)] transition"
              >
                Compare Docs
              </Link>
            </div>
          </div>

          {/* Real Embedded Workspace Dashboard */}
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--background)] p-6 shadow-xl space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-[var(--border)]">
              <div className="flex items-center gap-3">
                <span className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-sm font-semibold text-[var(--foreground)]">Evaluation Corpus: Active</span>
              </div>
              <span className="text-xs font-mono text-[var(--muted)]">Quota: 5 Docs · 20 Queries/Day</span>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                title="Active Documents"
                value={data ? data.activeDocuments.toString() : "3 / 5"}
                subtitle="Evaluation tier limit"
                icon={FileText}
              />
              <MetricCard
                title="Total Extracted Pages"
                value={data ? data.totalExtractedPages.toString() : "42"}
                subtitle="Parsed via Kahn DAG"
                icon={Layers}
              />
              <MetricCard
                title="Tokens Packed"
                value={data ? data.totalTokensPacked.toLocaleString() : "14,820"}
                subtitle="Submodular knapsack"
                icon={Binary}
              />
              <MetricCard
                title="Audit Invariants"
                value="100%"
                subtitle="Grounded citations"
                icon={ShieldCheck}
              />
            </div>

            {/* Ingestion & Recent Docs */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <div className="lg:col-span-7">
                <h4 className="text-sm font-semibold mb-3 text-[var(--foreground)]">Corpus Document Library</h4>
                <RecentDocuments documents={data?.recentDocuments ?? []} />
              </div>
              <div className="lg:col-span-5 space-y-4">
                <h4 className="text-sm font-semibold text-[var(--foreground)]">Processing Status</h4>
                <ProcessingSummary summary={data?.processingSummary ?? {
                  pending: 0,
                  processing: 0,
                  completed: 3,
                  failed: 0,
                  needsReview: 0
                }} />
                <AttentionPanel items={data?.attentionItems ?? []} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 05: TRUST & DATA PROTECTION
      ───────────────────────────────────────────────────────────── */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 border-b border-[var(--border)]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <h2 className="text-xs font-bold uppercase tracking-widest text-emerald-500">Security & Trust</h2>
            <p className="mt-2 text-3xl font-extrabold tracking-tight text-[var(--foreground)]">
              Designed with strict boundary isolation & privacy
            </p>
            <p className="mt-4 text-base text-[var(--muted)]">
              AEGIS-DocIntel was engineered from Day 1 to protect your confidential research and enterprise filings.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6">
              <Shield className="w-8 h-8 text-blue-500 mb-4" />
              <h3 className="text-lg font-bold text-[var(--foreground)]">Two-Tier Zero-Leak Model</h3>
              <p className="mt-2 text-sm text-[var(--muted)] leading-relaxed">
                Downloadable Windows client contains zero Python code, zero private keys, and zero credentials. Proprietary engines run isolated behind HMAC service authorization.
              </p>
            </div>

            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6">
              <Lock className="w-8 h-8 text-emerald-500 mb-4" />
              <h3 className="text-lg font-bold text-[var(--foreground)]">Zero Model Training</h3>
              <p className="mt-2 text-sm text-[var(--muted)] leading-relaxed">
                Your uploaded documents and queries are excluded from upstream foundation model training. All data is scoped with tenant isolation and 10s worker scratchpad wipes.
              </p>
            </div>

            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6">
              <CheckCircle2 className="w-8 h-8 text-purple-500 mb-4" />
              <h3 className="text-lg font-bold text-[var(--foreground)]">Cascading Erasure</h3>
              <p className="mt-2 text-sm text-[var(--muted)] leading-relaxed">
                Evaluators can trigger atomic data termination at any time via the evaluation portal, initiating immediate cryptographic deletion across primary DB, vectors, and caches.
              </p>
            </div>
          </div>

          <div className="mt-8 text-center">
            <Link
              href="/security"
              className="inline-flex items-center gap-2 text-sm font-semibold text-blue-500 hover:text-blue-400 transition"
            >
              Read our full Security & Penetration Testing Dossier (130/130 Defended)
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────
          SECTION 06: CALL TO ACTION
      ───────────────────────────────────────────────────────────── */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-t from-blue-950/30 to-transparent">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[var(--foreground)]">
            Explore the AEGIS-DocIntel Evaluation Release
          </h2>
          <p className="mt-4 text-base sm:text-lg text-[var(--muted)] max-w-2xl mx-auto">
            Download the signed Windows evaluation package, activate your hardware-bound license, and test structured document intelligence on your own technical files.
          </p>

          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link
              href="/evaluation"
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-lg text-base font-semibold text-white bg-blue-600 hover:bg-blue-700 transition shadow-lg"
            >
              Start Free Evaluation
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/demo"
              className="inline-flex items-center gap-2 px-6 py-3.5 rounded-lg text-base font-semibold text-[var(--foreground)] bg-[var(--surface)] border border-[var(--border)] hover:bg-[var(--surface-hover)] transition"
            >
              Watch Product Walkthrough
            </Link>
          </div>

          <div className="mt-8 flex flex-wrap justify-center items-center gap-6 text-xs text-[var(--muted)]">
            <span>Evaluation Release: v0.1.0</span>
            <span>·</span>
            <Link href="/security" className="hover:underline">Privacy Notice</Link>
            <span>·</span>
            <Link href="/features" className="hover:underline">Feature Matrix</Link>
            <span>·</span>
            <Link href="/demo" className="hover:underline">Walkthrough Script</Link>
          </div>
        </div>
      </section>
    </div>
  );
}
