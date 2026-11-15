import { test as base, Page } from "@playwright/test";
import { SYNTHETIC_DOCUMENTS, TestDocumentItem } from "./test-data";

export const test = base.extend<{
  mockDocumentsApi: (docs?: TestDocumentItem[]) => Promise<void>;
}>({
  mockDocumentsApi: async ({ page }, use) => {
    const setupMocks = async (customDocs?: TestDocumentItem[]) => {
      const docs = customDocs || SYNTHETIC_DOCUMENTS;
      await page.route("**/v1/documents**", async (route) => {
        if (route.request().method() === "GET") {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              items: docs,
              total: docs.length,
              page: 1,
              pageSize: 20,
            }),
          });
        } else if (route.request().method() === "POST") {
          const body = route.request().postData();
          await route.fulfill({
            status: 201,
            contentType: "application/json",
            body: JSON.stringify({
              id: "doc-new-uploaded-999",
              status: "queued",
              message: "Document accepted for processing",
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
