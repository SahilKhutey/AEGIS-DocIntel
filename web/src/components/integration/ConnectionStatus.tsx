"use client";

import React from "react";
import { Wifi, WifiOff, RefreshCw } from "lucide-react";

export type ConnectionState = "connected" | "reconnecting" | "disconnected";

export interface ConnectionStatusProps {
  status: ConnectionState;
  onReconnect?: () => void;
  className?: string;
}

export function ConnectionStatus({
  status,
  onReconnect,
  className = "",
}: ConnectionStatusProps) {
  const config = {
    connected: {
      label: "Live Synced",
      icon: Wifi,
      bg: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800",
      dot: "bg-emerald-500",
    },
    reconnecting: {
      label: "Reconnecting...",
      icon: RefreshCw,
      bg: "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-800",
      dot: "bg-amber-500 animate-ping",
    },
    disconnected: {
      label: "Disconnected",
      icon: WifiOff,
      bg: "bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-300 dark:border-rose-800",
      dot: "bg-rose-500",
    },
  }[status];

  const Icon = config.icon;

  return (
    <div
      role="status"
      aria-live="polite"
      className={`inline-flex items-center gap-2 px-2.5 py-1 text-xs font-medium rounded-full border ${config.bg} ${className}`}
    >
      <span className="relative flex h-2 w-2" aria-hidden="true">
        <span
          className={`relative inline-flex rounded-full h-2 w-2 ${config.dot}`}
        />
      </span>

      <Icon
        className={`w-3 h-3 ${status === "reconnecting" ? "animate-spin" : ""}`}
        aria-hidden="true"
      />

      <span>{config.label}</span>

      {status === "disconnected" && onReconnect && (
        <button
          type="button"
          onClick={onReconnect}
          className="ml-1 underline hover:text-rose-800 dark:hover:text-rose-200 focus:outline-none"
        >
          Retry
        </button>
      )}
    </div>
  );
}
