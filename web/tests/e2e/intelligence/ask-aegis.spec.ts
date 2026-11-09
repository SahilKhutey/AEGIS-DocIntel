import { expect, test } from "@playwright/test";

test.describe("Ask AEGIS", () => {
  test("renders the question workspace", async ({ page }) => {
    await page.goto("/ask");

    await expect(
      page.getByRole("heading", { name: "Ask AEGIS" }),
    ).toBeVisible();

    await expect(
      page.getByLabel("Ask AEGIS a question"),
    ).toBeVisible();
  });

  test("blocks an empty question", async ({ page }) => {
    await page.goto("/ask");

    await expect(
      page.getByRole("button", { name: "Ask AEGIS" }),
    ).toBeDisabled();
  });
});
