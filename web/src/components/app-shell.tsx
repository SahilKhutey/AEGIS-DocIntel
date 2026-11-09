"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  NAVIGATION,
  isNavigationItemActive,
} from "@/config/navigation";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname() ?? "/";

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>

      <header className="sticky top-0 z-40 border-b border-gray-200 bg-white">
        <div className="mx-auto flex min-h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link
            href="/"
            aria-label="AEGIS workspace home"
            className="flex items-center gap-3"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-700 font-bold text-white">
              A
            </span>
            <span className="font-bold tracking-tight text-gray-900">
              AEGIS
              <span className="ml-1.5 text-xs font-semibold text-blue-700">
                DocIntel
              </span>
            </span>
          </Link>

          <span className="hidden text-xs text-gray-500 sm:block">
            Document Intelligence Workbench
          </span>
        </div>

        <nav
          aria-label="Primary navigation"
          className="mx-auto hidden max-w-7xl gap-1 overflow-x-auto px-4 pb-2 md:flex sm:px-6 lg:px-8"
        >
          {NAVIGATION.map((group) => {
            const visibleItems = group.items.filter(
              (item) => item.status === "active",
            );

            if (visibleItems.length === 0) return null;

            return (
              <div key={group.id} className="flex items-center gap-1">
                <span className="px-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
                  {group.label}
                </span>

                {visibleItems.map((item) => {
                  const active = isNavigationItemActive(
                    pathname,
                    item,
                  );

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      aria-current={active ? "page" : undefined}
                      title={item.description}
                      className={[
                        "rounded-md px-3 py-2 text-sm transition-colors",
                        active
                          ? "bg-blue-50 font-semibold text-blue-700"
                          : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
                      ].join(" ")}
                    >
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            );
          })}
        </nav>

        <nav
          aria-label="Mobile navigation"
          className="flex gap-2 overflow-x-auto border-t border-gray-100 px-4 py-2 md:hidden"
        >
          {NAVIGATION.flatMap((group) => group.items)
            .filter((item) => item.status === "active")
            .map((item) => {
              const active = isNavigationItemActive(
                pathname,
                item,
              );

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={[
                    "whitespace-nowrap rounded-md px-3 py-2 text-xs",
                    active
                      ? "bg-blue-50 font-semibold text-blue-700"
                      : "text-gray-600 hover:bg-gray-100",
                  ].join(" ")}
                >
                  {item.label}
                </Link>
              );
            })}
        </nav>
      </header>

      <main
        id="main-content"
        tabIndex={-1}
        className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8 outline-none"
      >
        {children}
      </main>

      <footer className="mt-auto border-t border-gray-200 bg-white py-4">
        <div className="mx-auto max-w-7xl px-4 text-center text-xs text-gray-500">
          AEGIS-DocIntel · Evidence Grounding · Document Intelligence · Governance
        </div>
      </footer>
    </div>
  );
}
