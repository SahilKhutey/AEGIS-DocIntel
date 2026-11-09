"use client";

import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useDebounce } from "@/hooks/use-debounce";
import { isSafeInternalHref } from "@/lib/shell/route-utils";
import type { GlobalSearchResponse, SearchResult } from "@/features/search/types";

type GlobalSearchProps = {
  search?: (query: string) => Promise<GlobalSearchResponse>;
};

export function GlobalSearch({ search }: GlobalSearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const debouncedQuery = useDebounce(query.trim(), 300);

  useEffect(() => {
    if (!search || debouncedQuery.length < 2) {
      setResults([]);
      setLoading(false);
      setError(null);
      return;
    }

    let active = true;
    setLoading(true);
    setError(null);

    search(debouncedQuery)
      .then((response) => {
        if (active) setResults(response.items);
      })
      .catch(() => {
        if (active) {
          setError("Search is temporarily unavailable.");
          setResults([]);
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [debouncedQuery, search]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setQuery("");
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setQuery("");
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  const showResults = query.trim().length >= 2;

  return (
    <div className="relative w-full max-w-xl" ref={containerRef}>
      <div className="relative">
        <Search
          aria-hidden="true"
          className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted)] pointer-events-none"
        />

        <Input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search documents, evidence, reviews..."
          aria-label="Search AEGIS"
          role="combobox"
          aria-autocomplete="list"
          aria-controls="global-search-results"
          aria-expanded={showResults}
          className="pl-9 pr-9 h-9 text-xs sm:text-sm bg-[var(--surface)] border-[var(--border)]"
        />

        {query && (
          <Button
            variant="ghost"
            size="sm"
            className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0 text-[var(--muted)] hover:text-[var(--foreground)]"
            aria-label="Clear search"
            onClick={() => setQuery("")}
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </Button>
        )}
      </div>

      {showResults && (
        <section
          id="global-search-results"
          aria-label="Search results"
          className="absolute left-0 right-0 top-full z-50 mt-2 max-h-80 overflow-y-auto rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-md)]"
        >
          {loading && (
            <p role="status" className="p-3 text-xs text-[var(--muted)]">
              Searching…
            </p>
          )}

          {error && (
            <p role="alert" className="p-3 text-xs text-[var(--danger)] bg-red-50">
              {error}
            </p>
          )}

          {!loading && !error && results.length === 0 && (
            <p className="p-3 text-xs text-[var(--muted)] text-center">
              No matching results.
            </p>
          )}

          <ul className="divide-y divide-[var(--border)]">
            {results
              .filter((result) => isSafeInternalHref(result.href))
              .map((result) => (
                <li key={`${result.category}-${result.id}`}>
                  <Link
                    href={result.href}
                    onClick={() => setQuery("")}
                    className="block p-3 hover:bg-[var(--surface-muted)] transition-colors"
                  >
                    <span className="block text-xs font-semibold text-[var(--foreground)] truncate">
                      {result.title}
                    </span>
                    <span className="text-[11px] text-[var(--muted)] uppercase tracking-wide">
                      {result.category}
                      {result.description ? ` · ${result.description}` : ""}
                    </span>
                  </Link>
                </li>
              ))}
          </ul>
        </section>
      )}
    </div>
  );
}
