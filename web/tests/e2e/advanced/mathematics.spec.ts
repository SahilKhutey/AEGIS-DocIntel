import { test, expect } from "@playwright/test";

test.describe("Advanced Interfaces — Mathematical Representations (/mathematics)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/mathematics");
  });

  test("renders mathematics catalog and vector viewer", async ({ page }) => {
    await expect(page.getByText("Mathematical Representations & Formulations")).toBeVisible();
    await expect(page.getByText("Dense Semantic Embedding — Section 2.1")).toBeVisible();
    await expect(page.getByText("1,536")).toBeVisible();

    // Verify view toggle to table
    const tableBtn = page.getByRole("button", { name: /Table view/i });
    await tableBtn.click();
    await expect(page.getByText("Value (Raw float32)")).toBeVisible();

    // Verify switch back to heatmap
    const heatmapBtn = page.getByRole("button", { name: /Heatmap view/i });
    await heatmapBtn.click();
    await expect(page.getByText(/Dimensions \[0\.\.31\]/i)).toBeVisible();
  });

  test("interacts with matrix viewer cell selection", async ({ page }) => {
    await expect(page.getByText("Document Inter-Chunk Cosine Similarity Kernel")).toBeVisible();
    await expect(page.getByText("Click any cell to inspect value")).toBeVisible();

    // Click cell [0, 1]
    const cell = page.locator('td[title*="[0, 1]"]');
    await cell.click();
    await expect(page.getByText("Selected:")).toBeVisible();
    await expect(page.getByText(/Row 0/i)).toBeVisible();
  });

  test("navigates to formulas tab and displays LaTeX equations", async ({ page }) => {
    await expect(page.getByText("Dense Semantic Embedding — Section 2.1")).toBeVisible();
    const eqTab = page.getByRole("button", { name: /Formulas & Equations/i });
    await eqTab.click();

    await expect(page.getByText("Cosine Similarity Metric")).toBeVisible();
    await expect(page.getByText("Okapi BM25 Lexical Ranking Function")).toBeVisible();
    await expect(page.getByText("Unified Ising Hamiltonian for Conflict Optimization")).toBeVisible();
  });

  test("navigates to transformation trace tab", async ({ page }) => {
    await expect(page.getByText("Dense Semantic Embedding — Section 2.1")).toBeVisible();
    const traceTab = page.getByRole("button", { name: /Transformation Trace/i });
    await traceTab.click();

    await expect(page.getByText("Transformation Pipeline Trace")).toBeVisible();
    await expect(page.getByText("Raw Source Parsing & Cleaning")).toBeVisible();
    await expect(page.getByText("Dense Vector Embedding Inference")).toBeVisible();
    await expect(page.getByText("L2 Unit Hypersphere Normalization")).toBeVisible();
  });

  test("runs interactive unified math evaluator", async ({ page }) => {
    await expect(page.getByText("Dense Semantic Embedding — Section 2.1")).toBeVisible();
    const evalTab = page.getByRole("button", { name: /Unified Evaluator/i });
    await evalTab.click();

    await expect(page.getByText("Unified Math Evaluation")).toBeVisible();
    const evalBtn = page.getByRole("button", { name: /Run Evaluation/i });
    await evalBtn.click();

    await expect(page.getByText("Computed Output:")).toBeVisible();
  });
});
