import { test, expect } from "@playwright/test";

test.describe("Advanced Interfaces — Performance Monitoring (/monitoring)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/monitoring");
  });

  test("renders overall health banner and freshness indicator", async ({ page }) => {
    await expect(page.getByText("System Health & Performance Monitoring")).toBeVisible();
    await expect(page.getByText("All Systems Operational")).toBeVisible();
    await expect(page.getByText(/Freshness:/i)).toBeVisible();
  });

  test("displays service health cards with latencies and uptime", async ({ page }) => {
    await expect(page.getByText("Infrastructure & Dependent Services")).toBeVisible();
    await expect(page.getByText("FastAPI Application Gateway")).toBeVisible();
    await expect(page.getByText("PostgreSQL Metadata Store")).toBeVisible();
    await expect(page.getByText("HNSW Vector Database")).toBeVisible();
    await expect(page.getByText("Document Object Storage")).toBeVisible();
    await expect(page.getByText("Background Processing Workers")).toBeVisible();
  });

  test("displays latency percentiles and throughput metrics", async ({ page }) => {
    await expect(page.getByText("Request & Query Latency Distribution")).toBeVisible();
    await expect(page.getByText("P50 (Median)")).toBeVisible();
    await expect(page.getByText("P95 (SLA Threshold)")).toBeVisible();
    await expect(page.getByText("P99 (Tail Latency)")).toBeVisible();

    await expect(page.getByText("Throughput & Worker Concurrency")).toBeVisible();
    await expect(page.getByText("142")).toBeVisible(); // RPM
    await expect(page.getByText("18.5")).toBeVisible(); // chunks/sec
  });

  test("acknowledges active operational alert", async ({ page }) => {
    await expect(page.getByText("Operational Alerts & Notifications")).toBeVisible();
    await expect(page.getByText("Scheduled Maintenance Window")).toBeVisible();

    const ackBtn = page.getByRole("button", { name: /Acknowledge/i });
    await ackBtn.click();

    await expect(page.getByText("All systems operating within acceptable parameters.")).toBeVisible();
  });
});
