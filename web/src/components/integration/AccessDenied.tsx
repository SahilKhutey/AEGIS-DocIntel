"use client";

import React from "react";
import Link from "next/link";
import { ShieldAlert, ArrowLeft } from "lucide-react";

export interface AccessDeniedProps {
  requiredPermission?: string;
  resourceName?: string;
  onGoBack?: () => void;
}

export function AccessDenied({
  requiredPermission,
  resourceName = "this resource",
  onGoBack,
}: AccessDeniedProps) {
  return (
    <div
      role="alert"
      aria-labelledby="access-denied-title"
      aria-describedby="access-denied-desc"
      className="max-w-md mx-auto my-12 p-6 rounded-xl border border-red-200 dark:border-red-900/40 bg-red-50/50 dark:bg-red-950/20 text-center space-y-4"
    >
      <div className="w-12 h-12 mx-auto rounded-full bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 flex items-center justify-center">
        <ShieldAlert className="w-6 h-6" aria-hidden="true" />
      </div>

      <div className="space-y-1">
        <h2
          id="access-denied-title"
          className="text-lg font-semibold text-slate-900 dark:text-slate-100"
        >
          Access Denied
        </h2>
        <p
          id="access-denied-desc"
          className="text-sm text-slate-600 dark:text-slate-400"
        >
          Your account does not possess the necessary authorization to access{" "}
          <span className="font-medium text-slate-800 dark:text-slate-200">{resourceName}</span>.
        </p>
      </div>

      {requiredPermission && (
        <div className="text-xs font-mono px-3 py-1.5 rounded bg-red-100/70 dark:bg-red-900/30 text-red-700 dark:text-red-300 inline-block">
          Required permission: {requiredPermission}
        </div>
      )}

      <div className="pt-2 flex justify-center gap-3">
        {onGoBack ? (
          <button
            type="button"
            onClick={onGoBack}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
            Go Back
          </button>
        ) : (
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
            Back to Workspace
          </Link>
        )}
      </div>
    </div>
  );
}
