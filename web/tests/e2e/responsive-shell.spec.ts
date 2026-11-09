import { test, expect } from "@playwright/test";

test("mobile menu opens and closes", async ({ page }) => {
  await page.setViewportSize({
    width: 375,
    height: 812,
  });

  await page.goto("/");

  await page
    .getByRole("button", {
      name: "Open navigation",
    })
    .click();

  await expect(
    page.getByRole("dialog", {
      name: "Mobile navigation",
    })
  ).toBeVisible();

  await page.keyboard.press("Escape");

  await expect(
    page.getByRole("dialog", {
      name: "Mobile navigation",
    })
  ).toHaveCount(0);
});

test("desktop sidebar is visible", async ({ page }) => {
  await page.setViewportSize({
    width: 1440,
    height: 900,
  });

  await page.goto("/");

  await expect(
    page.getByRole("navigation", {
      name: /(main|primary) navigation/i,
    })
  ).toBeVisible();
});

test("shell does not overflow horizontally", async ({ page }) => {
  for (const width of [375, 768, 1024, 1440]) {
    await page.setViewportSize({
      width,
      height: 900,
    });

    await page.goto("/");

    const overflow = await page.evaluate(
      () =>
        document.documentElement.scrollWidth >
        document.documentElement.clientWidth
    );

    expect(overflow).toBe(false);
  }
});
