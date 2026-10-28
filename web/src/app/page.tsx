"use client";

import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-8">
      <div className="rounded-2xl bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-800 p-8 text-white shadow-lg">
        <div className="max-w-3xl">
          <span className="inline-block rounded-full bg-white/20 px-3 py-1 text-xs font-semibold uppercase tracking-wider backdrop-blur-sm">
            Workbench v1.0
          </span>
          <h1 className="mt-4 text-3xl font-extrabold sm:text-4xl tracking-tight">
            AEGIS Document Intelligence Workbench
          </h1>
          <p className="mt-3 text-base sm:text-lg text-blue-100 leading-relaxed">
            End-to-end evidence grounding, structured intelligence extraction, cross-document comparison,
            and human governance review.
          </p>
          <div className="mt-6 flex flex-wrap gap-4">
            <Link
              href="/documents"
              className="inline-flex items-center rounded-lg bg-white px-4 py-2.5 text-sm font-semibold text-blue-700 shadow hover:bg-blue-50 transition"
            >
              Document Workspace &rarr;
            </Link>
            <Link
              href="/reviews"
              className="inline-flex items-center rounded-lg border border-white/40 bg-white/10 px-4 py-2.5 text-sm font-semibold text-white hover:bg-white/20 transition backdrop-blur-sm"
            >
              Review Queue
            </Link>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="text-2xl mb-2">📄</div>
          <h2 className="text-base font-semibold text-gray-900">Document Workspace</h2>
          <p className="mt-1 text-sm text-gray-500">
            Upload, inspect indexing pipelines, view text chunks, and track processing states.
          </p>
          <Link href="/documents" className="mt-4 inline-block text-sm font-medium text-blue-600 hover:text-blue-800">
            Manage documents &rarr;
          </Link>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="text-2xl mb-2">💬</div>
          <h2 className="text-base font-semibold text-gray-900">Ask &amp; Evidence Explorer</h2>
          <p className="mt-1 text-sm text-gray-500">
            Ask questions over authorized documents and inspect strictly cited evidence snippets.
          </p>
          <Link href="/ask" className="mt-4 inline-block text-sm font-medium text-blue-600 hover:text-blue-800">
            Start query &rarr;
          </Link>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="text-2xl mb-2">⚖️</div>
          <h2 className="text-base font-semibold text-gray-900">Intelligence &amp; Compare</h2>
          <p className="mt-1 text-sm text-gray-500">
            Compare multi-document agreements, extract typed facts, and detect contradictions.
          </p>
          <Link href="/compare" className="mt-4 inline-block text-sm font-medium text-blue-600 hover:text-blue-800">
            Compare agreements &rarr;
          </Link>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="text-2xl mb-2">🛡️</div>
          <h2 className="text-base font-semibold text-gray-900">Human Review &amp; Audit</h2>
          <p className="mt-1 text-sm text-gray-500">
            Review candidate facts and conflicts, submit versioned decisions, and record audit trails.
          </p>
          <Link href="/reviews" className="mt-4 inline-block text-sm font-medium text-blue-600 hover:text-blue-800">
            Open review queue &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
