import React from "react";
import Link from "next/link";
import { AlertCircle, AlertTriangle, ArrowRight } from "lucide-react";
import type { AttentionItem } from "../types";

export type AttentionPanelProps = {
  items: AttentionItem[];
};

export function AttentionPanel({ items }: AttentionPanelProps) {
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-emerald-200 dark:border-emerald-900/40 bg-emerald-50/30 dark:bg-emerald-950/20 p-5 shadow-2xs">
        <div className="flex items-center gap-3">
          <div className="rounded-full bg-emerald-100 dark:bg-emerald-900/60 p-2 text-emerald-700 dark:text-emerald-300">
            <AlertCircle className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-emerald-900 dark:text-emerald-200">
              Operational Status Healthy
            </h3>
            <p className="text-xs text-emerald-700/80 dark:text-emerald-300/80 mt-0.5">
              No failed jobs, unprocessed document errors, or urgent review blockers in this workspace.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-amber-200 dark:border-amber-900/50 bg-amber-50/20 dark:bg-amber-950/20 p-6 shadow-xs">
      <div className="flex items-center gap-2 pb-3 border-b border-amber-200/60 dark:border-amber-900/40">
        <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400" />
        <h2 className="text-base font-semibold text-amber-900 dark:text-amber-200">
          Requires Attention ({items.length})
        </h2>
      </div>

      <ul className="mt-3 divide-y divide-amber-200/40 dark:divide-amber-900/30">
        {items.map((item) => (
          <li key={item.id} className="py-3 flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-[var(--foreground)]">
                {item.title}
              </p>
              <p className="text-xs text-[var(--muted)] mt-0.5">
                {item.description}
              </p>
            </div>
            <Link
              href={item.link}
              className="inline-flex items-center text-xs font-semibold text-[var(--primary)] hover:underline whitespace-nowrap mt-1"
            >
              Resolve <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
