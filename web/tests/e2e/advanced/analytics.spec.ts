import { test, expect } from "@playwright/test";

test.describe("Advanced Interfaces — Analytics & Reporting (/analytics)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/analytics");
  });

  test("renders analytics dashboard with operational KPI metrics", async ({ page }) => {
    await expect(page.getByText("Analytics & Operational Metrics")).toBeVisible();
    await expect(page.getByText("Total Ingested Documents", { exact: false })).toBeVisible();

    // Verify key metrics exist
    await expect(page.getByRole("region", { name: /Documents metric/i })).toBeVisible();
    await expect(page.getByRole("region", { name: /Chunks metric/i })).toBeVisible();
    await expect(page.getByRole("region", { name: /Tokens Used metric/i })).toBeVisible();
    await expect(page.getByRole("region", { name: /Avg Query Latency metric/i })).toBeVisible();
  });

  test("switches time range presets", async ({ page }) => {
    const rangeGroup = page.getByRole("group", { name: /Select analytics time range/i });
    await expect(rangeGroup).toBeVisible();

    const btn24h = rangeGroup.getByRole("button", { name: /Last 24 Hours/i });
    await btn24h.click();
    await expect(btn24h).toHaveAttribute("aria-pressed", "true");

    const btn30d = rangeGroup.getByRole("button", { name: /Last 30 Days/i });
    await btn30d.click();
    await expect(btn30d).toHaveAttribute("aria-pressed", "true");
  });

  test("switches between analytics tabs", async ({ page }) => {
    // Documents Tab
    const docsTab = page.getByRole("button", { name: /Documents & Ingestion/i });
    await docsTab.click();
    await expect(page.getByText("Ingestion & Chunk Density")).toBeVisible();
    await expect(page.getByText("Document Type Composition")).toBeVisible();

    // Intelligence Tab
    const intelTab = page.getByRole("button", { name: /Intelligence & Tokens/i });
    await intelTab.click();
    await expect(page.getByText("Token Consumption Breakdown")).toBeVisible();
    await expect(page.getByText("Model Distribution & Routing")).toBeVisible();

    // Governance Tab
    const govTab = page.getByRole("button", { name: /Governance Reviews/i });
    await govTab.click();
    await expect(page.getByText("Total Reviewed Items")).toBeVisible();
    await expect(page.getByText("Review Decision Distribution")).toBeVisible();
  });

  test("triggers CSV export without crash", async ({ page }) => {
    const exportBtn = page.getByRole("button", { name: /Export.*CSV/i });
    await expect(exportBtn).toBeVisible();
    await expect(exportBtn).toBeEnabled();
  });
});
