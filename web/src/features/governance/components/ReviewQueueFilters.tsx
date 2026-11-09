import React from "react";
import type { ReviewQueueFiltersState } from "../types";

interface ReviewQueueFiltersProps {
  filters: ReviewQueueFiltersState;
  onChange: (updated: Partial<ReviewQueueFiltersState>) => void;
  countsByStatus?: Record<string, number>;
}

const STATUS_TABS = [
  { id: "all", label: "All Items" },
  { id: "pending", label: "Pending" },
  { id: "in_review", label: "In Review" },
  { id: "approved", label: "Approved" },
  { id: "corrected", label: "Corrected" },
  { id: "rejected", label: "Rejected" },
  { id: "needs_evidence", label: "Needs Evidence" },
];

export function ReviewQueueFilters({
  filters,
  onChange,
  countsByStatus,
}: ReviewQueueFiltersProps) {
  return (
    <div className="space-y-4">
      {/* Search and Dropdowns Row */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search by candidate, attribute, document ID..."
            value={filters.searchQuery}
            onChange={(e) => onChange({ searchQuery: e.target.value })}
            className="w-full rounded-lg border border-gray-300 pl-9 pr-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
          />
          <svg
            className="absolute left-3 top-2.5 h-4 w-4 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        <div className="flex items-center gap-2">
          {/* Candidate Type selector */}
          <select
            value={filters.candidateType}
            onChange={(e) =>
              onChange({
                candidateType: e.target.value as "all" | "fact" | "conflict",
              })
            }
            aria-label="Filter by candidate type"
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 focus:outline-none"
          >
            <option value="all">All Types</option>
            <option value="fact">Facts Only</option>
            <option value="conflict">Conflicts Only</option>
          </select>

          {/* Assignment selector */}
          <select
            value={filters.assignment}
            onChange={(e) =>
              onChange({
                assignment: e.target.value as "all" | "unassigned" | "assigned",
              })
            }
            aria-label="Filter by assignment"
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 focus:outline-none"
          >
            <option value="all">All Assignments</option>
            <option value="unassigned">Unassigned</option>
            <option value="assigned">Assigned</option>
          </select>
        </div>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex flex-wrap items-center gap-1.5 border-b border-gray-200 pb-3" role="tablist">
        {STATUS_TABS.map((tab) => {
          const isActive = filters.status === tab.id;
          const count = countsByStatus?.[tab.id];

          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={isActive}
              type="button"
              onClick={() => onChange({ status: tab.id })}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition flex items-center gap-1.5 ${
                isActive
                  ? "bg-blue-600 text-white shadow-xs font-semibold"
                  : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
              }`}
            >
              <span>{tab.label}</span>
              {count !== undefined && (
                <span
                  className={`rounded-full px-1.5 py-0.2 text-[10px] font-mono ${
                    isActive ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-600"
                  }`}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
