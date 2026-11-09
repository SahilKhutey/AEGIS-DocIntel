export type ServiceStatus = "healthy" | "degraded" | "unhealthy";

export interface ServiceHealthItem {
  id: string;
  name: string;
  category: "core" | "storage" | "database" | "compute" | "external";
  status: ServiceStatus;
  latencyMs: number;
  uptimePercent: number;
  lastChecked: string;
  details?: string;
}

export interface LatencyPercentileData {
  p50: number;
  p90: number;
  p95: number;
  p99: number;
  unit: "ms";
  targetP95: number;
}

export interface ThroughputMetrics {
  requestsPerMinute: number;
  chunksPerSecond: number;
  activeWorkers: number;
  queueDepth: number;
  maxWorkers: number;
}

export interface OperationalAlert {
  id: string;
  severity: "critical" | "warning" | "info";
  title: string;
  message: string;
  serviceId: string;
  timestamp: string;
  acknowledged: boolean;
}

export interface MonitoringSnapshot {
  overallStatus: ServiceStatus;
  timestamp: string;
  services: ServiceHealthItem[];
  latencyPercentiles: LatencyPercentileData;
  throughput: ThroughputMetrics;
  alerts: OperationalAlert[];
}
