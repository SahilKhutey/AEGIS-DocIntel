import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ServiceHealthList } from "@/features/monitoring/components/ServiceHealthList";
import { LatencyPercentiles } from "@/features/monitoring/components/LatencyPercentiles";
import { ThroughputChart } from "@/features/monitoring/components/ThroughputChart";
import type { ServiceHealthItem } from "@/features/monitoring/types";

describe("Performance Monitoring components", () => {
  const mockServices: ServiceHealthItem[] = [
    {
      id: "api-gw",
      name: "FastAPI Application Gateway",
      category: "core",
      status: "healthy",
      latencyMs: 12,
      uptimePercent: 99.98,
      lastChecked: "2026-11-09T10:00:00.000Z",
      details: "Workers active",
    },
    {
      id: "vector-store",
      name: "HNSW Vector Database",
      category: "database",
      status: "degraded",
      latencyMs: 85,
      uptimePercent: 99.5,
      lastChecked: "2026-11-09T10:00:00.000Z",
    },
  ];

  it("renders services with names, categories, and status badges", () => {
    render(<ServiceHealthList services={mockServices} />);
    expect(screen.getByText("FastAPI Application Gateway")).toBeInTheDocument();
    expect(screen.getByText("HNSW Vector Database")).toBeInTheDocument();
    expect(screen.getByText("Healthy")).toBeInTheDocument();
    expect(screen.getByText("Degraded")).toBeInTheDocument();
    expect(screen.getByText("12ms")).toBeInTheDocument();
  });

  it("renders LatencyPercentiles with P50, P90, P95, P99 values", () => {
    const lat = {
      p50: 85,
      p90: 165,
      p95: 210,
      p99: 420,
      unit: "ms" as const,
      targetP95: 300,
    };
    render(<LatencyPercentiles percentiles={lat} />);
    expect(screen.getByText("P50 (Median)")).toBeInTheDocument();
    expect(screen.getByText("85ms")).toBeInTheDocument();
    expect(screen.getByText("P95 (SLA Threshold)")).toBeInTheDocument();
    expect(screen.getByText("210ms")).toBeInTheDocument();
    expect(screen.getByText("P99 (Tail Latency)")).toBeInTheDocument();
    expect(screen.getByText("420ms")).toBeInTheDocument();
  });

  it("renders ThroughputChart with RPM and worker capacity", () => {
    const throughput = {
      requestsPerMinute: 142,
      chunksPerSecond: 18.5,
      activeWorkers: 4,
      maxWorkers: 8,
      queueDepth: 2,
    };
    render(<ThroughputChart metrics={throughput} />);
    expect(screen.getByText("142")).toBeInTheDocument();
    expect(screen.getByText("18.5")).toBeInTheDocument();
    expect(screen.getByText("4/8")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });
});
