"use client";

import React, { useState } from "react";

type Props = {
  onSearch: (query: string) => void;
  loading?: boolean;
};

export function RetrievalSearch({ onSearch, loading = false }: Props) {
  const [query, setQuery] = useState("");

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        const value = query.trim();
        if (value && !loading) {
          onSearch(value);
        }
      }}
      className="flex flex-col gap-3 sm:flex-row"
    >
      <input
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search across your documents..."
        aria-label="Search documents"
        className="min-w-0 flex-1 rounded-xl border border-gray-300 p-3 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
      <button
        type="submit"
        disabled={!query.trim() || loading}
        className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-xs hover:bg-blue-500 disabled:opacity-50 transition"
      >
        {loading ? "Searching..." : "Search"}
      </button>
    </form>
  );
}
