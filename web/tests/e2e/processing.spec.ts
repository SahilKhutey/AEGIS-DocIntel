import { test, expect } from "@playwright/test";

test.describe("Processing Monitor", () => {
  test.beforeEach(async ({ page }) => {
    // Intercept jobs endpoint
    await page.route("**/api/v1/jobs*", async (route) => {
      const url = new URL(route.request().url());
      const statusParam = url.searchParams.get("status");

      const allJobs = [
        {
          job_id: "job-run-001",
          tenant_id: "default",
          job_type: "index_document",
          resource_id: "doc-beta-002",
          status: "running",
          attempt: 1,
          max_attempts: 3,
          version: 1,
          idempotency_key: "idem-001",
          input_fingerprint: "fp-001",
          requested_by: "user-1",
          payload: { filename: "security_policy_v2.docx" },
          created_at: "2026-11-02T10:00:00Z",
          updated_at: "2026-11-02T10:02:00Z",
        },
        {
          job_id: "job-fail-002",
          tenant_id: "default",
          job_type: "index_document",
          resource_id: "doc-gamma-003",
          status: "failed",
          attempt: 3,
          max_attempts: 3,
          version: 1,
          idempotency_key: "idem-002",
          input_fingerprint: "fp-002",
          requested_by: "user-1",
          error_code: "Corrupt PDF stream encountered at page 4",
          payload: { filename: "vendor_contract_2026.pdf" },
          created_at: "2026-11-03T10:00:00Z",
          updated_at: "2026-11-03T10:05:00Z",
        },
        {
          job_id: "job-succ-003",
          tenant_id: "default",
          job_type: "extract_facts",
          resource_id: "doc-alpha-001",
          status: "succeeded",
          attempt: 1,
          max_attempts: 3,
          version: 1,
          idempotency_key: "idem-003",
          input_fingerprint: "fp-003",
          requested_by: "user-1",
          payload: { filename: "acme_q3_financial_report.pdf" },
          created_at: "2026-11-01T10:00:00Z",
          updated_at: "2026-11-01T10:05:00Z",
        },
      ];

      let items = allJobs;
      if (statusParam) {
        items = allJobs.filter((j) => j.status === statusParam);
      }

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items,
          next_cursor: null,
        }),
      });
    });

    // Intercept retry endpoint
    await page.route("**/api/v1/jobs/*/retry", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          message: "Job retry scheduled.",
        }),
      });
    });
  });

  test("displays processing monitor with jobs list and status badges", async ({ page }) => {
    await page.goto("/processing");

    await expect(page.getByRole("heading", { name: "Processing Monitor" })).toBeVisible();
    await expect(page.getByText("security_policy_v2.docx")).toBeVisible();
    await expect(page.getByText("vendor_contract_2026.pdf")).toBeVisible();
    await expect(page.getByText("acme_q3_financial_report.pdf")).toBeVisible();

    await expect(page.getByLabel("Job status: Running")).toBeVisible();
    await expect(page.getByLabel("Job status: Failed")).toBeVisible();
    await expect(page.getByLabel("Job status: Succeeded")).toBeVisible();
  });

  test("filters jobs by status tabs", async ({ page }) => {
    await page.goto("/processing");

    // Click "Failed" status filter button
    await page.getByRole("button", { name: "Failed" }).click();

    await expect(page.getByText("vendor_contract_2026.pdf")).toBeVisible();
    await expect(page.getByText("security_policy_v2.docx")).not.toBeVisible();
    await expect(page.getByText("acme_q3_financial_report.pdf")).not.toBeVisible();
  });

  test("allows retrying a failed job", async ({ page }) => {
    await page.goto("/processing");

    const retryBtn = page.getByRole("button", { name: /retry failed job/i });
    await expect(retryBtn).toBeVisible();
    await retryBtn.click();
  });

  test("displays empty state when no jobs exist", async ({ page }) => {
    await page.route("**/api/v1/jobs*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], next_cursor: null }),
      });
    });

    await page.goto("/processing");
    await expect(page.getByText(/no processing jobs/i)).toBeVisible();
  });
});
