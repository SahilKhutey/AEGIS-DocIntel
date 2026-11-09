"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, LogIn, RefreshCw } from "lucide-react";

export interface SessionExpiredProps {
  onRefresh?: () => Promise<void> | void;
  onSignIn?: () => void;
  isRefreshing?: boolean;
}

export function SessionExpired({
  onRefresh,
  onSignIn,
  isRefreshing = false,
}: SessionExpiredProps) {
  const router = useRouter();

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="session-expired-title"
      aria-describedby="session-expired-desc"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm"
    >
      <div className="w-full max-w-sm rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-2xl space-y-5 text-center">
        <div className="w-12 h-12 mx-auto rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 flex items-center justify-center">
          <AlertTriangle className="w-6 h-6" aria-hidden="true" />
        </div>

        <div className="space-y-1">
          <h2
            id="session-expired-title"
            className="text-base font-semibold text-slate-900 dark:text-slate-100"
          >
            Session Expired
          </h2>
          <p
            id="session-expired-desc"
            className="text-xs text-slate-600 dark:text-slate-400"
          >
            Your sovereign session credentials have expired. Please refresh your session or re-authenticate to continue.
          </p>
        </div>

        <div className="flex flex-col gap-2 pt-2">
          {onRefresh && (
            <button
              type="button"
              disabled={isRefreshing}
              onClick={onRefresh}
              className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium rounded-lg bg-sky-600 text-white hover:bg-sky-500 disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-sky-500"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`}
                aria-hidden="true"
              />
              {isRefreshing ? "Refreshing Session..." : "Refresh Session"}
            </button>
          )}

          <button
            type="button"
            onClick={
              onSignIn ||
              (() => {
                router.push("/");
              })
            }
            className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <LogIn className="w-3.5 h-3.5" aria-hidden="true" />
            Re-authenticate
          </button>
        </div>
      </div>
    </div>
  );
}
