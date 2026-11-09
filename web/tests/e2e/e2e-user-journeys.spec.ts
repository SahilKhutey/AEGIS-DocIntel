import { test, expect, type Route } from "@playwright/test";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "*",
};

async function handleCorsMock(route: Route, jsonBody: unknown, status = 200) {
  if (route.request().method() === "OPTIONS") {
    await route.fulfill({
      status: 204,
      headers: CORS_HEADERS,
    });
    return;
  }
  await route.fulfill({
    status,
    headers: CORS_HEADERS,
    contentType: "application/json",
    body: JSON.stringify(jsonBody),
  });
}

test.describe("WP-UI-08 User Journey 1: Document Intelligence Workflow", () => {
  test("complete document inspection to grounded question answering journey", async ({
    page,
  }) => {
    // 1. Mock document API responses
    await page.route("**/api/v1/documents*", async (route) => {
      await handleCorsMock(route, {
        items: [
          {
            doc_id: "doc-1",
            filename: "Financial_Report_Q3.pdf",
            status: "ready",
            page_count: 12,
            chunk_count: 48,
            is_scanned: false,
            language: "en",
            created_at: "2026-11-09T10:00:00Z",
            indexed_at: "2026-11-09T10:05:00Z",
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
      });
    });

    await page.route("**/v1/documents*", async (route) => {
      await handleCorsMock(route, {
        items: [
          {
            id: "doc-1",
            name: "Financial_Report_Q3.pdf",
            status: "completed",
            file_type: "pdf",
            size_bytes: 1048576,
            created_at: "2026-11-09T10:00:00Z",
            updated_at: "2026-11-09T10:05:00Z",
          },
        ],
        total: 1,
      });
    });

    // 2. Mock grounded Q&A endpoint
    await page.route("**/api/v1/ask*", async (route) => {
      await handleCorsMock(route, {
        status: "grounded",
        answer: "The Q3 revenue grew by 18% with net operating margin of 24%.",
        request_id: "req-q3-001",
        confidence: 0.94,
        insufficient_evidence: false,
        citations: [
          {
            evidence_id: "ev-1",
            document_id: "Financial_Report_Q3.pdf",
            page_number: 4,
            section_path: ["Financials", "Executive Summary"],
          },
        ],
        evidence: [
          {
            evidence_id: "ev-1",
            document_id: "Financial_Report_Q3.pdf",
            quote: "Net operating margin reached 24% in Q3.",
            page_number: 4,
            section_path: ["Financials", "Executive Summary"],
          },
        ],
      });
    });

    // 1. Enter Document Library
    await page.goto("/documents");
    await expect(page.locator("main").getByRole("heading", { name: "Documents", level: 1 })).toBeVisible();

    // 2. Document table search input and upload button
    await expect(page.getByRole("textbox", { name: "Search documents" })).toBeVisible();
    await expect(page.getByRole("button", { name: /Upload Document/i })).toBeVisible();

    // 3. Navigate to Ask AEGIS
    await page.goto("/ask");
    await expect(page.getByRole("heading", { name: /Ask AEGIS/i })).toBeVisible();

    // 4. Ask a question
    const input = page.locator("#aegis-question");
    await expect(input).toBeVisible();
    await input.fill("What were the key financial results in Q3?");
    const submitBtn = page.getByRole("button", { name: "Ask AEGIS" });
    await submitBtn.click();

    // 5. Answer and grounded citation appear
    await expect(page.getByText(/The Q3 revenue grew by 18%/i)).toBeVisible();
    await expect(page.getByText(/Financial_Report_Q3.pdf/i).first()).toBeVisible();
  });
});

test.describe("WP-UI-08 User Journey 2: Comparison & Governance Workflow", () => {
  test("comparison to review queue and sovereign decision submission", async ({
    page,
  }) => {
    page.on("console", (msg) => console.log("JOURNEY 2 LOG:", msg.type(), msg.text()));
    page.on("requestfailed", (req) =>
      console.log("JOURNEY 2 FAILED REQ:", req.url(), req.failure()?.errorText)
    );

    // Mock multi-document API responses
    await page.route("**/api/v1/documents*", async (route) => {
      await handleCorsMock(route, {
        items: [
          {
            doc_id: "doc-1",
            filename: "Contract_Alpha_2026.pdf",
            status: "ready",
            page_count: 8,
            chunk_count: 24,
            is_scanned: false,
            language: "en",
            created_at: "2026-11-09T09:00:00Z",
          },
          {
            doc_id: "doc-2",
            filename: "Contract_Beta_2026.pdf",
            status: "ready",
            page_count: 10,
            chunk_count: 30,
            is_scanned: false,
            language: "en",
            created_at: "2026-11-09T09:30:00Z",
          },
        ],
        total: 2,
        page: 1,
        page_size: 20,
      });
    });

    // Mock governance review queue and metrics
    await page.route(/\/api\/v1\/reviews/, async (route) => {
      const url = route.request().url();
      if (url.includes("/metrics")) {
        await handleCorsMock(route, {
          total_items: 12,
          decided_count: 8,
          approval_rate: 0.75,
          correction_rate: 0.15,
          rejection_rate: 0.10,
          evidence_failure_rate: 0.05,
          feedback_categories: {},
        });
      } else if (url.includes("/history")) {
        await handleCorsMock(route, [
          {
            event_id: "evt-1",
            review_id: "REV-2026-001",
            sequence: 1,
            tenant_id: "tenant-default",
            actor_id: "system",
            action: "create",
            previous_status: "pending",
            new_status: "pending",
            previous_version: 1,
            new_version: 1,
            rationale: "Automated conflict detection during multi-doc indexing",
            timestamp: "2026-11-09T09:45:00Z",
          },
        ]);
      } else if (url.includes("REV-2026-001")) {
        await handleCorsMock(route, {
          review_id: "REV-2026-001",
          tenant_id: "tenant-default",
          candidate_id: "cand-conflict-01",
          candidate_type: "conflict",
          document_id: "doc-1",
          status: "pending",
          version: 1,
          candidate_data: {
            subject: "Governing Law",
            attribute: "Jurisdiction Clause",
            value: "Delaware vs New York",
            raw_value: "Delaware vs New York",
          },
          created_at: "2026-11-09T09:45:00Z",
          updated_at: "2026-11-09T09:45:00Z",
        });
      } else {
        await handleCorsMock(route, {
          items: [
            {
              review_id: "REV-2026-001",
              tenant_id: "tenant-default",
              candidate_id: "cand-conflict-01",
              candidate_type: "conflict",
              document_id: "doc-1",
              status: "pending",
              version: 1,
              candidate_data: {
                subject: "Governing Law",
                attribute: "Jurisdiction Clause",
                value: "Delaware vs New York",
                raw_value: "Delaware vs New York",
              },
              created_at: "2026-11-09T09:45:00Z",
              updated_at: "2026-11-09T09:45:00Z",
            },
          ],
          next_cursor: null,
        });
      }
    });

    // 1. Enter Compare Documents
    await page.goto("/compare");
    await expect(page.getByRole("heading", { name: /Document Intelligence &.*Comparison/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Compare Selected Documents/i })).toBeVisible();

    // 2. Enter Governance Reviews
    await page.goto("/reviews");
    await expect(page.getByRole("heading", { name: /Review Queue/i })).toBeVisible();

    // 3. Open a review record
    const reviewLink = page.getByRole("link", { name: /Governing Law/i }).first();
    await expect(reviewLink).toBeVisible();
    await reviewLink.click();

    // Wait for URL navigation to /reviews/REV-2026-001
    await page.waitForURL(/.*\/reviews\/REV-2026-001/);

    // 4. Verify Fact Verification and Conflict Resolution tabs render
    await expect(page.getByRole("tab", { name: /Fact Verification/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole("tab", { name: /Conflict Resolution/i })).toBeVisible();

    // 5. Audit history tab exists
    await expect(page.getByRole("tab", { name: /Audit Trail/i })).toBeVisible();
  });
});

test.describe("WP-UI-08 User Journey 3: Engineering & Operations Workflow", () => {
  test("analytics to mathematical models, pipelines, monitoring, and developer platform", async ({
    page,
  }) => {
    // 1. Analytics KPIs & time range selector
    await page.goto("/analytics");
    await expect(page.getByRole("heading", { name: /Analytics & Operational Metrics/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Last 7 Days/i })).toBeVisible();

    // 2. Mathematical representations
    await page.goto("/mathematics");
    await expect(page.getByRole("heading", { name: /Mathematical Representations/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Vectors & Matrices/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Formulas & Equations/i })).toBeVisible();

    // 3. Background processing pipelines
    await page.goto("/pipelines");
    await expect(page.getByRole("heading", { name: /Pipeline Execution Runs/i })).toBeVisible();
    await expect(page.getByPlaceholder(/Search pipelines/i)).toBeVisible();

    // 4. Service monitoring & SLAs
    await page.goto("/monitoring");
    await expect(page.getByRole("heading", { name: /System Health & Performance Monitoring/i })).toBeVisible();
    await expect(page.getByText(/FastAPI Application Gateway/i)).toBeVisible();

    // 5. Developer portal & OpenAPI Explorer
    await page.goto("/developer");
    await expect(page.getByRole("heading", { name: /Developer Platform & Integration Center/i })).toBeVisible();
    await expect(page.getByRole("button", { name: "API Credentials" })).toBeVisible();
    await expect(page.getByRole("button", { name: "API Explorer" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Webhooks" })).toBeVisible();
  });
});
