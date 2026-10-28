"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface AppShellProps {
  children: React.ReactNode;
}

const NAV_ITEMS = [
  { href: "/documents", label: "Documents", icon: "📄" },
  { href: "/ask", label: "Ask & Evidence", icon: "💬" },
  { href: "/compare", label: "Intelligence & Compare", icon: "⚖️" },
  { href: "/reviews", label: "Review Queue", icon: "🛡️" },
];

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans">
      <header className="sticky top-0 z-40 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <Link href="/documents" className="flex items-center gap-2.5">
                <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
                  A
                </div>
                <div>
                  <span className="text-base font-bold text-gray-900 tracking-tight">AEGIS</span>
                  <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 ml-1.5 px-1.5 py-0.5 bg-blue-50 rounded">
                    DocIntel
                  </span>
                </div>
              </Link>

              <nav className="hidden md:flex space-x-1" aria-label="Main Navigation">
                {NAV_ITEMS.map((item) => {
                  const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        isActive
                          ? "bg-blue-50 text-blue-700 font-semibold"
                          : "text-gray-600 hover:text-gray-900 hover:bg-gray-100/70"
                      }`}
                      aria-current={isActive ? "page" : undefined}
                    >
                      <span>{item.icon}</span>
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </nav>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-2 text-xs text-gray-500 bg-gray-100/80 px-2.5 py-1.5 rounded-md border border-gray-200/60">
                <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
                <span className="font-mono">Tenant: default-tenant</span>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden border-t border-gray-100 px-4 py-2 flex overflow-x-auto gap-1">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`whitespace-nowrap px-3 py-1.5 rounded-md text-xs font-medium ${
                  isActive
                    ? "bg-blue-50 text-blue-700 font-semibold"
                    : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      <footer className="bg-white border-t border-gray-200 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 text-center text-xs text-gray-400">
          AEGIS-DocIntel &bull; Evidence Grounding, Document Intelligence &amp; Governance Workbench
        </div>
      </footer>
    </div>
  );
}
