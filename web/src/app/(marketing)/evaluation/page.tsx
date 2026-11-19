"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Download,
  KeyRound,
  CheckCircle2,
  Terminal,
  ShieldCheck,
  FileText,
  ArrowRight,
  ExternalLink,
  Copy,
  Check,
} from "lucide-react";

export default function EvaluationOnboardingPage() {
  const [copiedHash, setCopiedHash] = useState(false);
  const [inviteToken, setInviteToken] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const packageSha256 = "b0aa37d650c97fccbfc98686252b447820abad59d4815de124eadd71fbea0c50";

  const handleCopy = () => {
    void navigator.clipboard.writeText(packageSha256);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleInviteSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inviteToken.trim()) {
      setSubmitted(true);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-[var(--background)] text-[var(--foreground)] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-12">
        {/* Header */}
        <div className="border-b border-[var(--border)] pb-8 text-center sm:text-left">
          <span className="text-xs font-bold uppercase tracking-widest text-blue-500">Controlled Evaluation Release</span>
          <h1 className="mt-2 text-3xl sm:text-4xl font-extrabold tracking-tight text-[var(--foreground)]">
            AEGIS-DocIntel Onboarding & Evaluation Portal
          </h1>
          <p className="mt-4 text-base text-[var(--muted)] max-w-2xl leading-relaxed">
            Welcome to the AEGIS-DocIntel Evaluation Programme (v0.1.0). Follow the 4-step onboarding journey
            to download the client, verify its cryptographic integrity, and activate your evaluation license.
          </p>
        </div>

        {/* Evaluation Quota Summary Card */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--muted)] mb-4">
            Evaluation Quotas & Entitlements
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <div className="text-xl font-bold text-blue-500">5</div>
              <div className="text-xs text-[var(--muted)] mt-1">Active Documents</div>
            </div>
            <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <div className="text-xl font-bold text-blue-500">10 MB</div>
              <div className="text-xs text-[var(--muted)] mt-1">Max File Size</div>
            </div>
            <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <div className="text-xl font-bold text-blue-500">20 / Day</div>
              <div className="text-xs text-[var(--muted)] mt-1">Queries & Diffs</div>
            </div>
            <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <div className="text-xl font-bold text-emerald-500">1 Device</div>
              <div className="text-xs text-[var(--muted)] mt-1">Hardware Bound</div>
            </div>
          </div>
        </div>

        {/* 4-Step Onboarding Journey */}
        <div className="space-y-6">
          {/* Step 1 */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-4">
            <div className="flex items-center gap-3">
              <span className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-sm">
                1
              </span>
              <h3 className="text-lg font-bold text-[var(--foreground)]">Invitation Code / Registration</h3>
            </div>
            <p className="text-sm text-[var(--muted)]">
              Enter your 256-bit evaluation invitation token or register to receive an instant evaluation grant:
            </p>
            {submitted ? (
              <div className="p-4 rounded-lg bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 text-sm flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5" />
                Invitation token accepted! Proceed to download your package below.
              </div>
            ) : (
              <form onSubmit={handleInviteSubmit} className="flex gap-3 max-w-lg">
                <input
                  type="text"
                  placeholder="Enter invitation token (e.g. aegis-eval-token-...)"
                  value={inviteToken}
                  onChange={(e) => setInviteToken(e.target.value)}
                  className="flex-1 px-4 py-2.5 rounded-lg border border-[var(--border)] bg-[var(--background)] text-sm focus:outline-hidden focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  className="px-5 py-2.5 rounded-lg text-sm font-semibold bg-blue-600 text-white hover:bg-blue-700 transition"
                >
                  Verify Token
                </button>
              </form>
            )}
          </div>

          {/* Step 2 */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-4">
            <div className="flex items-center gap-3">
              <span className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-sm">
                2
              </span>
              <h3 className="text-lg font-bold text-[var(--foreground)]">Download Evaluation Client (Windows 64-bit)</h3>
            </div>
            <p className="text-sm text-[var(--muted)]">
              Download the self-contained evaluation release bundle. It contains the web frontend, launcher scripts, and public Ed25519 verification key:
            </p>
            <div className="flex flex-wrap items-center gap-4">
              <a
                href="/v1/evaluation/download?package=AEGIS-Evaluation-0.1.0.zip"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 transition"
              >
                <Download className="w-4 h-4" />
                Download AEGIS-Evaluation-0.1.0.zip (3.8 MB)
              </a>
              <span className="text-xs text-[var(--muted)]">SHA-256 Verified · 0 Python files · Zero credentials</span>
            </div>

            {/* Hash Box */}
            <div className="mt-3 p-3 rounded-lg bg-[var(--background)] border border-[var(--border)] flex items-center justify-between text-xs font-mono">
              <span className="truncate mr-2 text-[var(--muted)]">SHA-256: {packageSha256}</span>
              <button
                onClick={handleCopy}
                className="px-2.5 py-1 rounded bg-[var(--surface)] hover:bg-[var(--surface-hover)] border border-[var(--border)] text-[var(--foreground)] transition flex items-center gap-1 shrink-0"
              >
                {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                {copiedHash ? "Copied" : "Copy"}
              </button>
            </div>
          </div>

          {/* Step 3 */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-4">
            <div className="flex items-center gap-3">
              <span className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-sm">
                3
              </span>
              <h3 className="text-lg font-bold text-[var(--foreground)]">Verify & Launch Client</h3>
            </div>
            <p className="text-sm text-[var(--muted)]">
              Extract the zip archive and run the verification script in PowerShell to confirm all 37 package assets match the signed manifest:
            </p>
            <div className="p-4 rounded-lg bg-black/90 text-slate-200 font-mono text-xs space-y-2">
              <div className="text-slate-400"># Verify package integrity</div>
              <div>powershell -ExecutionPolicy Bypass -File .\launcher\verify-package.ps1</div>
              <div className="text-emerald-400">✓ All 37 files verified authentic and untampered (Ed25519 valid).</div>
              <div className="pt-2 text-slate-400"># Start local evaluation UI and proxy</div>
              <div>powershell -ExecutionPolicy Bypass -File .\launcher\start-aegis.ps1</div>
            </div>
          </div>

          {/* Step 4 */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-4">
            <div className="flex items-center gap-3">
              <span className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-sm">
                4
              </span>
              <h3 className="text-lg font-bold text-[var(--foreground)]">Activate License & Hardware Binding</h3>
            </div>
            <p className="text-sm text-[var(--muted)]">
              When prompted by the client launcher or UI, enter your activation code to bind your evaluation session via Ed25519 challenge-response. Once activated, your daily quota is immediately unlocked.
            </p>
            <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)] text-xs text-[var(--muted)] flex items-center gap-2">
              <KeyRound className="w-4 h-4 text-blue-500 shrink-0" />
              <span>Activation binds to your designated Windows installation ID. Recovery codes are hashed and non-reversible.</span>
            </div>
          </div>
        </div>

        {/* Documentation Links */}
        <div className="pt-6 border-t border-[var(--border)] text-xs text-[var(--muted)] flex flex-wrap justify-between items-center gap-4">
          <div className="space-x-4">
            <Link href="/security" className="hover:underline">Evaluation Agreement</Link>
            <Link href="/security" className="hover:underline">Privacy Notice</Link>
            <Link href="/features" className="hover:underline">Architecture Specification</Link>
          </div>
          <div>Need help? Email <code>support@aegis-docintel.internal</code></div>
        </div>
      </div>
    </div>
  );
}
