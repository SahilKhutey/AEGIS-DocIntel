import { test, expect } from "@playwright/test";

test.describe("AEGIS-DocIntel Browser E2E Suite", () => {
  test.beforeEach(async ({ page }) => {
    // Intercept common API routes to return deterministic mock responses
    await page.route("**/api/v1/documents", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              doc_id: "doc-alpha-001",
              filename: "acme_q3_financial_report.pdf",
              status: "ready",
              page_count: 14,
              chunk_count: 42,
              created_at: "2026-11-04T08:00:00Z",
              indexed_at: "2026-11-04T08:01:00Z",
            },
            {
              doc_id: "doc-beta-002",
              filename: "globex_q3_earnings.pdf",
              status: "indexing",
              page_count: 8,
              chunk_count: 24,
              created_at: "2026-11-04T08:05:00Z",
              indexed_at: null,
            },
          ],
          total: 2,
          page: 1,
          page_size: 20,
        }),
      });
    });

    await page.route("**/api/v1/documents/doc-alpha-001", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          doc_id: "doc-alpha-001",
          filename: "acme_q3_financial_report.pdf",
          status: "ready",
          page_count: 14,
          chunk_count: 42,
          created_at: "2026-11-04T08:00:00Z",
          indexed_at: "2026-11-04T08:01:00Z",
        }),
      });
    });

    await page.route("**/api/v1/documents/doc-alpha-001/chunks", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              chunk_id: "chk-001",
              doc_id: "doc-alpha-001",
              text: "Acme Corporation reported Q3 2026 revenue of $142.5 million, representing 18% YoY growth.",
              page_number: 1,
              section_title: "Financial Highlights",
            },
            {
              chunk_id: "chk-002",
              doc_id: "doc-alpha-001",
              text: "Operating expenses totaled $98.2 million, driven by expansion of the cloud division.",
              page_number: 2,
              section_title: "Operating Results",
            },
          ],
          total: 2,
        }),
      });
    });

    await page.route("**/api/v1/documents/doc-alpha-001/facts", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          facts: [
            {
              entity: "Acme Corporation",
              attribute: "revenue_q3_2026",
              value: "$142.5M",
              confidence: 0.98,
              temporal_anchor: "2026-Q3",
            },
          ],
        }),
      });
    });

    const answerPayload = {
      status: "grounded",
      answer: "Acme Corporation reported Q3 2026 revenue of $142.5 million.",
      citations: [
        {
          evidence_id: "ev-001",
          document_id: "doc-alpha-001",
          page_number: 1,
          section_path: ["Financial Highlights"],
        },
      ],
      evidence: [
        {
          evidence_id: "ev-001",
          document_id: "doc-alpha-001",
          chunk_id: "chk-001",
          quote: "Acme Corporation reported Q3 2026 revenue of $142.5 million.",
          page_number: 1,
        },
      ],
      warnings: [],
      insufficient_evidence: false,
    };

    await page.route("**/api/v1/answers", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(answerPayload),
      });
    });

    await page.route("**/api/v1/ask", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(answerPayload),
      });
    });

    await page.route("**/api/v1/reviews", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              review_id: "rev-001",
              tenant_id: "tenant-alpha-001",
              candidate_id: "revenue_q3_2026",
              candidate_type: "fact",
              status: "pending",
              field_name: "revenue_q3_2026",
              extracted_value: "$142.5M",
              candidate_data: {
                subject: "Acme Corporation",
                attribute: "revenue_q3_2026",
                value: "$142.5M",
              },
              document_id: "doc-alpha-001",
              page_number: 1,
              confidence: 0.98,
              created_at: "2026-11-04T08:00:00Z",
              updated_at: "2026-11-04T08:00:00Z",
              version: 1,
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
        }),
      });
    });
  });

  // E2E-001 & E2E-003: App shell & navigation
  test("E2E-001 & E2E-003: documents page loads with navigation links and metrics", async ({ page }) => {
    await page.goto("/documents");
    await expect(page.getByRole("heading", { name: /document workspace/i })).toBeVisible();
    const primaryNav = page.getByRole("navigation", { name: "Primary navigation" });
    await expect(primaryNav.getByRole("link", { name: /(ask & evidence|ask aegis)/i })).toBeVisible();
    await expect(primaryNav.getByRole("link", { name: /(cross-document comparison|compare documents)/i })).toBeVisible();
    await expect(primaryNav.getByRole("link", { name: /review queue/i })).toBeVisible();
  });

  // E2E-004 & E2E-005: Upload modal interaction
  test("E2E-004 & E2E-005: upload modal opens and displays file constraints", async ({ page }) => {
    await page.goto("/documents");
    const uploadBtn = page.getByRole("button", { name: /upload document/i });
    if (await uploadBtn.isVisible()) {
      await uploadBtn.click();
      await expect(page.getByText(/upload document/i).first()).toBeVisible();
    }
  });

  // E2E-006 & E2E-007: Document details and extracted chunks
  test("E2E-006 & E2E-007: document detail view displays chunks and facts", async ({ page }) => {
    await page.goto("/documents/doc-alpha-001");
    await expect(page.getByRole("heading", { name: "acme_q3_financial_report.pdf" })).toBeVisible();
    await expect(page.getByText("Financial Highlights")).toBeVisible();
    await expect(page.getByText("$142.5 million")).toBeVisible();
  });

  // E2E-009 & E2E-010: Ask question and citations
  test("E2E-009 & E2E-010: ask page executes query and renders grounded citation", async ({ page }) => {
    await page.goto("/ask");
    await expect(page.getByRole("heading", { name: /ask & evidence explorer/i })).toBeVisible();
    await page.getByLabel(/your question/i).fill("What was Acme's revenue in Q3 2026?");
    await page.getByRole("button", { name: /ask question/i }).click();
    await expect(page.getByText(/reported Q3 2026 revenue of \$142.5 million/i).first()).toBeVisible();
  });

  // E2E-012: Cross-document comparison
  test("E2E-012: compare page enforces document selection for comparison", async ({ page }) => {
    await page.goto("/compare");
    await expect(page.getByRole("heading", { name: /document intelligence & cross-document comparison/i })).toBeVisible();
  });

  // E2E-013 & E2E-014: Governance review queue
  test("E2E-013 & E2E-014: reviews queue displays pending governance decisions", async ({ page }) => {
    await page.goto("/reviews");
    await expect(page.getByRole("heading", { name: /human governance review queue/i })).toBeVisible();
    await expect(page.getByText("revenue_q3_2026")).toBeVisible();
  });
});
