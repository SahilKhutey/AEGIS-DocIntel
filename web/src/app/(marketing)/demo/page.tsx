"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Play,
  Pause,
  RotateCcw,
  Clock,
  CheckCircle2,
  FileText,
  Search,
  GitCompare,
  ShieldCheck,
  ArrowRight,
  Sparkles,
} from "lucide-react";

type Scene = {
  id: number;
  timeRange: string;
  duration: string;
  title: string;
  narration: string;
  screenAction: string;
  badge: string;
};

const SCENES: Scene[] = [
  {
    id: 1,
    timeRange: "00:00 – 00:08",
    duration: "8s",
    title: "Scene 1: The Problem",
    narration: "Working with complex documents usually means fighting formatting, losing context, and cross-referencing files manually.",
    screenAction: "Display overlapping dense PDF windows with complex multi-column hardware schematics and tables.",
    badge: "The Fragmented Document Problem",
  },
  {
    id: 2,
    timeRange: "00:08 – 00:18",
    duration: "10s",
    title: "Scene 2: Introduce AEGIS Workspace",
    narration: "Meet AEGIS-DocIntel: an integrated platform designed to turn complex documents into structured, grounded intelligence.",
    screenAction: "Smooth transition to AEGIS home dashboard showing active Document Library, system metrics, and quota monitors.",
    badge: "AEGIS-DocIntel Evaluation 0.1.0",
  },
  {
    id: 3,
    timeRange: "00:18 – 00:32",
    duration: "14s",
    title: "Scene 3: Ingestion & Spatial DAG Order",
    narration: "AEGIS doesn't just dump raw text. It maps layout geometry, heading trees, and multi-column reading order using spatial algorithms.",
    screenAction: "Drag-and-drop synthetic hardware spec PDF. Live parser displays layout extraction, Kahn DAG sorting, and table preservation.",
    badge: "Layout-Aware Spatial Parsing",
  },
  {
    id: 4,
    timeRange: "00:32 – 00:47",
    duration: "15s",
    title: "Scene 4: Grounded Coordinate Retrieval",
    narration: "Ask precise questions and get answers grounded directly in the text, backed by exact bounding-box coordinates you can verify.",
    screenAction: "Submit query: 'What is peak throughput?' Answer highlights exact bounding box in PDF viewer: [42, 110, 280, 145].",
    badge: "100% Grounded Coordinate Citations",
  },
  {
    id: 5,
    timeRange: "00:47 – 01:00",
    duration: "13s",
    title: "Scene 5: Topological Comparison",
    narration: "Compare document revisions instantly to surface contradictions, modified metrics, and altered specifications.",
    screenAction: "Compare v1 vs v2 specs. Interactive diff matrix highlights 450 -> 620 TFLOPS and 220W -> 285W discrepancy in amber.",
    badge: "Topological Discrepancy Detection",
  },
  {
    id: 6,
    timeRange: "01:00 – 01:15",
    duration: "15s",
    title: "Scene 6: Call To Action & Evaluation",
    narration: "Experience a better document intelligence workflow. Download the controlled evaluation package and share your feedback today.",
    screenAction: "Evaluation portal with direct download button, Ed25519 signature verification pill, and community feedback links.",
    badge: "Controlled Evaluation Release",
  },
];

export default function DemoPage() {
  const [selectedScene, setSelectedScene] = useState<Scene>(SCENES[0]);

  return (
    <div className="flex flex-col min-h-screen bg-[var(--background)] text-[var(--foreground)] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-10">
        {/* Header */}
        <div className="border-b border-[var(--border)] pb-8">
          <span className="text-xs font-bold uppercase tracking-widest text-blue-500">Walkthrough & Demo</span>
          <h1 className="mt-2 text-3xl sm:text-4xl font-extrabold tracking-tight text-[var(--foreground)]">
            AEGIS-DocIntel 75-Second Product Walkthrough
          </h1>
          <p className="mt-4 text-base text-[var(--muted)] max-w-3xl leading-relaxed">
            Every second of our Product Hunt walkthrough demonstrates real, unsimulated capabilities running on our
            synthetic evaluation corpus. Explore the scene storyboard, voiceover narration, and verified visual cues below.
          </p>
        </div>

        {/* Video Player Mock / Scene Inspector */}
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-xl space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-[var(--border)]">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold px-2.5 py-1 rounded bg-blue-500/10 text-blue-500 font-mono">
                {selectedScene.timeRange}
              </span>
              <span className="text-xs font-semibold text-[var(--foreground)]">{selectedScene.title}</span>
            </div>
            <span className="text-xs font-medium px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-500">
              {selectedScene.badge}
            </span>
          </div>

          {/* Simulated Player Canvas */}
          <div className="relative aspect-video rounded-xl bg-slate-950 border border-slate-800 flex flex-col justify-between p-6 overflow-hidden">
            <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
              <span>AEGIS_PRODUCT_DEMO_75S.MP4</span>
              <span>1080P · 60FPS · UNSIMULATED</span>
            </div>

            <div className="my-auto text-center max-w-xl mx-auto space-y-3">
              <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-blue-500/20 text-blue-400">
                {selectedScene.badge}
              </span>
              <p className="text-lg sm:text-xl font-bold text-white leading-relaxed">
                "{selectedScene.narration}"
              </p>
              <p className="text-xs text-slate-400">
                Action: {selectedScene.screenAction}
              </p>
            </div>

            <div className="space-y-2">
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-blue-500 h-full transition-all duration-300"
                  style={{ width: `${(selectedScene.id / 6) * 100}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                <span>Current: {selectedScene.timeRange.split(" – ")[0]}</span>
                <span>Total: 01:15 (75s)</span>
              </div>
            </div>
          </div>

          {/* Scene Selector Stepper */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            {SCENES.map((scene) => (
              <button
                key={scene.id}
                onClick={() => setSelectedScene(scene)}
                className={`p-3 rounded-lg border text-left transition text-xs ${
                  selectedScene.id === scene.id
                    ? "border-blue-500 bg-blue-500/10 text-[var(--foreground)] font-semibold"
                    : "border-[var(--border)] bg-[var(--background)] text-[var(--muted)] hover:text-[var(--foreground)]"
                }`}
              >
                <div className="font-mono text-[10px] text-blue-500">{scene.timeRange}</div>
                <div className="mt-1 truncate">{scene.title.split(": ")[1]}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Script & Voiceover Details */}
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-4">
          <h3 className="text-base font-bold text-[var(--foreground)]">Scene Narration & Screen Direction</h3>
          <div className="space-y-3 text-sm">
            <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <span className="text-xs font-bold text-blue-500 uppercase tracking-wider block mb-1">Narration (Voiceover):</span>
              <p className="text-[var(--foreground)] italic">"{selectedScene.narration}"</p>
            </div>
            <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--border)]">
              <span className="text-xs font-bold text-emerald-500 uppercase tracking-wider block mb-1">Visual Screen Action:</span>
              <p className="text-[var(--muted)]">{selectedScene.screenAction}</p>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="pt-6 border-t border-[var(--border)] flex items-center justify-between">
          <Link href="/features" className="text-sm font-semibold text-blue-500 hover:text-blue-400">
            &larr; Review Technical Features
          </Link>
          <Link href="/evaluation" className="px-6 py-2.5 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 transition">
            Launch Evaluation Now
          </Link>
        </div>
      </div>
    </div>
  );
}
