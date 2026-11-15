import { test as base } from "@playwright/test";
import { SYNTHETIC_REVIEWS, SyntheticReviewItem } from "./test-data";

export const test = base.extend<{
  mockReviewsApi: (reviews?: SyntheticReviewItem[]) => Promise<void>;
}>({
  mockReviewsApi: async ({ page }, use) => {
    const setupMocks = async (customReviews?: SyntheticReviewItem[]) => {
      const items = customReviews || SYNTHETIC_REVIEWS;
      await page.route("**/v1/reviews**", async (route) => {
        if (route.request().method() === "GET") {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              items,
              total: items.length,
              pendingCount: items.filter((i) => i.status === "pending_review").length,
            }),
          });
        } else if (route.request().method() === "POST") {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              status: "success",
              persistedAt: new Date().toISOString(),
              auditEventId: "audit-evt-gov-decision-001",
            }),
          });
        } else {
          await route.continue();
        }
      });
    };
    await use(setupMocks);
  },
});

export { expect } from "@playwright/test";
