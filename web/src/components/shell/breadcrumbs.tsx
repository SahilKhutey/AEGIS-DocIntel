"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { usePathname } from "next/navigation";
import { getBreadcrumbs } from "@/lib/shell/breadcrumbs";

export function Breadcrumbs() {
  const pathname = usePathname() || "/";
  const items = getBreadcrumbs(pathname);

  return (
    <nav aria-label="Breadcrumb" className="mb-5">
      <ol className="flex flex-wrap items-center gap-1.5 text-xs sm:text-sm">
        {items.map((item, index) => {
          const current = index === items.length - 1;

          return (
            <li
              key={`${item.label}-${index}`}
              className="flex items-center gap-1.5"
            >
              {index > 0 && (
                <ChevronRight
                  aria-hidden="true"
                  className="h-3.5 w-3.5 text-[var(--muted)] shrink-0"
                />
              )}

              {item.href && !current ? (
                <Link
                  href={item.href}
                  className="text-[var(--muted)] hover:text-[var(--foreground)] hover:underline transition-colors"
                >
                  {item.label}
                </Link>
              ) : (
                <span
                  aria-current={current ? "page" : undefined}
                  className={
                    current
                      ? "font-semibold text-[var(--foreground)]"
                      : "text-[var(--muted)]"
                  }
                >
                  {item.label}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
