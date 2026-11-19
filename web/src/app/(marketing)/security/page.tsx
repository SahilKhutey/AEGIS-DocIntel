"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Lock,
  Server,
  FileCheck2,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Database,
  KeyRound,
  FileText,
} from "lucide-react";

export default function SecurityTrustCenterPage() {
  return (
    <div className="flex flex-col min-h-screen bg-[var(--background)] text-[var(--foreground)] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-12">
        {/* Header */}
        <div className="border-b border-[var(--border)] pb-8">
          <span className="text-xs font-bold uppercase tracking-widest text-emerald-500">Trust & Compliance</span>
          <h1 className="mt-2 text-3xl sm:text-4xl font-extrabold tracking-tight text-[var(--foreground)]">
            AEGIS-DocIntel Security, Privacy & Compliance Architecture
          </h1>
          <p className="mt-4 text-base text-[var(--muted)] max-w-3xl leading-relaxed">
            AEGIS-DocIntel separates client presentation, public gateway ingress, and private engine execution
            into distinct cryptographic trust boundaries to guarantee total data isolation for every evaluator.
          </p>
        </div>

        {/* 1. Two-Tier Zero-Leak Model */}
        <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 space-y-4">
          <div className="flex items-center gap-3">
            <span className="p-2.5 rounded-lg bg-blue-500/10 text-blue-500">
              <Server className="w-6 h-6" />
            </span>
            <div>
              <h2 className="text-xl font-bold text-[var(--foreground)]">1. Two-Tier Zero-Leak Architecture</h2>
              <span className="text-xs font-mono text-blue-400">Strict Boundary Enforcement (PROT-FINAL-05)</span>
            </div>
          </div>
          <p className="text-sm text-[var(--muted)] leading-relaxed">
            Unlike desktop monolithic tools that ship raw Python code, proprietary weights, and credentials directly to the client computer, AEGIS enforces an air-tight distribution boundary:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div className="p-4 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <h3 className="text-xs font-semibold text-blue-400 uppercase tracking-wider">Downloadable Client Package</h3>
              <ul className="mt-2 space-y-1 text-xs text-[var(--muted)]">
                <li>&bull; 0 Python source files or bytecode</li>
                <li>&bull; 0 Private cryptographic keys</li>
                <li>&bull; 0 Hardcoded cloud or LLM credentials</li>
                <li>&bull; Only compiled Next.js UI, PowerShell/POSIX launcher scripts, and public Ed25519 verify key</li>
              </ul>
            </div>
            <div className="p-4 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Remote Isolated Engine</h3>
              <ul className="mt-2 space-y-1 text-xs text-[var(--muted)]">
                <li>&bull; Strict HMAC-SHA256 authenticated service requests</li>
                <li>&bull; Tenant-scoped queries: <code>WHERE tenant_id = :id</code></li>
                <li>&bull; Ephemeral document parser scratchpads (deleted &le; 10s)</li>
                <li>&bull; Response sanitizer automatically strips IPs and DB URIs</li>
              </ul>
            </div>
          </div>
        </section>

        {/* 2. Penetration Testing Certification */}
        <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 space-y-4">
          <div className="flex items-center gap-3">
            <span className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-500">
              <ShieldCheck className="w-6 h-6" />
            </span>
            <div>
              <h2 className="text-xl font-bold text-[var(--foreground)]">2. Independent Adversarial Validation</h2>
              <span className="text-xs font-mono text-emerald-400">130 / 130 Attack Vectors Defended (PROT-FINAL-03)</span>
            </div>
          </div>
          <p className="text-sm text-[var(--muted)] leading-relaxed">
            The evaluation release was tested against a sophisticated adversary model assuming full root access to the Windows client machine, memory tampering, token forgery, and HTTP verb manipulation:
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <div className="font-semibold text-emerald-500">Client Tampering</div>
              <div className="text-[11px] text-[var(--muted)]">10/10 Defended</div>
            </div>
            <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <div className="font-semibold text-emerald-500">Auth & Key Forgery</div>
              <div className="text-[11px] text-[var(--muted)]">12/12 Defended</div>
            </div>
            <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <div className="font-semibold text-emerald-500">Tenant IDOR Denial</div>
              <div className="text-[11px] text-[var(--muted)]">10/10 Defended</div>
            </div>
            <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <div className="font-semibold text-emerald-500">Quota Race Resistance</div>
              <div className="text-[11px] text-[var(--muted)]">10/10 Defended</div>
            </div>
            <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <div className="font-semibold text-emerald-500">Session Abuse</div>
              <div className="text-[11px] text-[var(--muted)]">10/10 Defended</div>
            </div>
            <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <div className="font-semibold text-emerald-500">Engine Perimeter</div>
              <div className="text-[11px] text-[var(--muted)]">10/10 Defended</div>
            </div>
            <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <div className="font-semibold text-emerald-500">API Abuse & Injections</div>
              <div className="text-[11px] text-[var(--muted)]">20/20 Defended</div>
            </div>
            <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <div className="font-semibold text-emerald-500">IP & Secret Exposure</div>
              <div className="text-[11px] text-[var(--muted)]">15/15 Defended</div>
            </div>
          </div>
        </section>

        {/* 3. Data Protection & Model Training Policy */}
        <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-8 space-y-4">
          <div className="flex items-center gap-3">
            <span className="p-2.5 rounded-lg bg-purple-500/10 text-purple-500">
              <Lock className="w-6 h-6" />
            </span>
            <div>
              <h2 className="text-xl font-bold text-[var(--foreground)]">3. Data Protection & Zero Model Training</h2>
              <span className="text-xs font-mono text-purple-400">Legal & Regulatory Assurance (PROT-FINAL-07)</span>
            </div>
          </div>
          <div className="space-y-3 text-sm text-[var(--muted)] leading-relaxed">
            <p>
              <strong>Zero Model Training Invariant:</strong> Under our third-party supplier agreements and evaluation contract, customer document payloads, extracted layout trees, embeddings, and query prompts are strictly excluded from upstream LLM model training.
            </p>
            <p>
              <strong>Regulatory Framework Mapping:</strong> The AEGIS compliance programme has been cross-mapped to India Digital Personal Data Protection Act 2023 (DPDP), EU General Data Protection Regulation (GDPR), ISO/IEC 27001:2022, and SOC 2 Trust Services Criteria.
            </p>
            <p>
              <strong>Cascading Data Erasure:</strong> Evaluators can execute a full cryptographic wipe of their tenant corpus at any time via <code>POST /v1/evaluation/termination-request</code>. This immediately cascades deletions across primary storage, vector indices, and temporary caches.
            </p>
          </div>
        </section>

        {/* CTA */}
        <div className="pt-6 border-t border-[var(--border)] flex items-center justify-between">
          <Link href="/" className="text-sm font-semibold text-blue-500 hover:text-blue-400">
            &larr; Back to Landing Page
          </Link>
          <Link href="/evaluation" className="px-6 py-2.5 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 transition">
            Start Free Evaluation
          </Link>
        </div>
      </div>
    </div>
  );
}
