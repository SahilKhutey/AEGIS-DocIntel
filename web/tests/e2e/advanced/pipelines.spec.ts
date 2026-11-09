import { test, expect } from "@playwright/test";

test.describe("Advanced Interfaces — Pipeline Visualization (/pipelines)", () => {
  test("renders pipeline runs list with filters and status badges", async ({ page }) => {
    await page.goto("/pipelines");

    await expect(page.getByText("Pipeline Execution Runs")).toBeVisible();
    await expect(page.getByText("job-run-9021")).toBeVisible();
    await expect(page.getByText("Q3_Financial_Review.pdf")).toBeVisible();
    await expect(page.getByText("job-run-9023")).toBeVisible();
    await expect(page.getByText("Corrupted_Tax_Report.pdf")).toBeVisible();

    // Filter by completed
    const select = page.locator("select");
    await select.selectOption("completed");
    await expect(page.getByText("job-run-9021")).toBeVisible();
    await expect(page.getByText("job-run-9023")).not.toBeVisible();
  });

  test("navigates to pipeline run detail and displays DAG graph", async ({ page }) => {
    await page.goto("/pipelines/job-run-9021");

    await expect(page.getByText("job-run-9021")).toBeVisible();
    await expect(page.getByText("Execution DAG & Stage Lifecycle")).toBeVisible();

    // Verify stage nodes exist
    await expect(page.getByRole("button", { name: /Document Ingestion/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /OCR & Vision Extraction/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Dense Embedding Generation/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /HNSW Vector Graph Indexation/i })).toBeVisible();

    // Verify event trail
    await expect(page.getByText("Chronological Event Trail")).toBeVisible();
    await expect(page.getByText("Pipeline run completed successfully")).toBeVisible();
  });

  test("displays failure diagnostics and retry button on failed run", async ({ page }) => {
    await page.goto("/pipelines/job-run-9023");

    await expect(page.getByText("job-run-9023")).toBeVisible();
    const retryBtn = page.getByRole("button", { name: /Retry Pipeline/i });
    await expect(retryBtn).toBeVisible();

    // Click OCR failed stage
    const ocrStage = page.getByRole("button", { name: /OCR & Vision Extraction/i });
    await ocrStage.click();

    await expect(page.getByText("Failure Error Code: OCR_TIMEOUT_EXCEEDED")).toBeVisible();
    await expect(page.getByText("Tesseract worker exceeded 30000ms deadline")).toBeVisible();

    // Trigger retry
    await retryBtn.click();
    await expect(page.getByText("Job job-run-9023 queued for retry execution.")).toBeVisible();
  });
});
