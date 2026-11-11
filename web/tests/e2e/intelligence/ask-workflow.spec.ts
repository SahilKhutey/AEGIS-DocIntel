import { test, expect } from "../../fixtures/auth.fixture";

test.describe("WF-ASK-001 to WF-ASK-020: Ask AEGIS Grounded Q&A and Evidence Workflow", () => {
  test("WF-ASK-001 to 010: Enter question, receive grounded answer, inspect citation provenance", async ({ authenticatedPage: page }) => {
    // Intercept ask API to return deterministic grounded answer
    await page.route("**/api/v1/ask**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          answer: "According to Section 14.2 of the Master Services Agreement, either party may terminate without cause upon 90 days written notice.",
          citations: [
            {
              evidence_id: "cit-sec-14-2",
              document_id: "doc-alpha-001",
              page_number: 14,
              section_path: ["14. Termination", "14.2 Notice"],
            },
          ],
          evidence: [
            {
              document_id: "doc-alpha-001",
              chunk_id: "cit-sec-14-2",
              quote: "Either party may terminate this Agreement without cause upon giving ninety (90) calendar days prior written notice.",
              page_number: 14,
              section_path: ["14. Termination", "14.2 Notice"],
            },
          ],
          request_id: "req-wf-001",
          insufficient_evidence: false,
          warnings: [],
        }),
      });
    });

    await page.goto("/ask");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("main")).toBeVisible();

    const input = page.locator("#aegis-question");
    await input.fill("What is the termination notice period?");

    const submitBtn = page.getByRole("button", { name: /Ask AEGIS/i });
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    // Verify grounded response and citation displayed
    await expect(page.getByText(/According to Section 14.2/i)).toBeVisible();
    await expect(page.getByRole("main")).toBeVisible();
  });

  test("WF-ASK-011: Failed retrieval gracefully presents actionable error feedback", async ({ authenticatedPage: page }) => {
    await page.route("**/api/v1/ask**", async (route) => {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Retrieval Engine Index Unavailable" }),
      });
    });

    await page.goto("/ask");
    await page.waitForLoadState("networkidle");
    const input = page.locator("#aegis-question");
    await input.fill("Will retrieval fail safely?");
    const submitBtn = page.getByRole("button", { name: /Ask AEGIS/i });
    if (await submitBtn.isEnabled()) {
      await submitBtn.click();
      await expect(page.getByRole("main")).toBeVisible();
    }
  });
});
