import { expect, test } from "@playwright/test";

test.describe("Evidence Explorer", () => {
  test("renders evidence explorer page and scope control", async ({ page }) => {
    await page.goto("/intelligence/evidence");

    await expect(
      page.getByRole("heading", { name: /Evidence Explorer & Provenance/i }),
    ).toBeVisible();

    await expect(page.getByLabel(/Active Document Evidence Scope/i)).toBeVisible();
  });
});
