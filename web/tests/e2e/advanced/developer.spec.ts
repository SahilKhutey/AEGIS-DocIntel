import { test, expect } from "@playwright/test";

test.describe("Advanced Interfaces — Developer Platform (/developer)", () => {
  test("renders developer platform and provisions new API key with secret warning", async ({ page }) => {
    await page.goto("/developer");

    await expect(page.getByText("Developer Platform & Integration Center")).toBeVisible();
    await expect(page.getByText("Production Ingestion Pipeline")).toBeVisible();

    const genBtn = page.getByRole("button", { name: /Generate API Key/i });
    await genBtn.click();

    await expect(page.getByText("Provision New API Key")).toBeVisible();
    await page.getByLabel(/Key Identifier/i).fill("Test Automation Key");

    const submitBtn = page.getByRole("button", { name: /Generate Credential/i });
    await submitBtn.click();

    // Verify one-time secret alert appears
    await expect(page.getByText("Save your secret key now. It will never be displayed again!")).toBeVisible();
    await expect(page.getByText(/aegis_live_sec_/i)).toBeVisible();

    // Dismiss one-time warning
    await page.getByText("I have stored this secret safely").click();
    await expect(page.getByText("Test Automation Key")).toBeVisible();
  });

  test("explores OpenAPI documentation and switches code language", async ({ page }) => {
    await page.goto("/developer/api");

    await expect(page.getByText("OpenAPI REST Endpoints")).toBeVisible();
    await expect(page.getByRole("button", { name: /GET.*\/v1\/admin\/stats/i })).toBeVisible();

    const pythonBtn = page.getByRole("button", { name: /Python/i });
    await pythonBtn.click();
    await expect(page.getByText("import requests")).toBeVisible();

    const tsBtn = page.getByRole("button", { name: /TypeScript/i });
    await tsBtn.click();
    await expect(page.getByText("const response = await fetch")).toBeVisible();
  });

  test("validates webhook URL and prevents SSRF localhost entry", async ({ page }) => {
    await page.goto("/developer/webhooks");

    await expect(page.getByText("Webhook Subscriptions")).toBeVisible();
    const regBtn = page.getByRole("button", { name: /Register Webhook/i });
    await regBtn.click();

    await page.getByLabel(/Destination HTTPS Endpoint URL/i).fill("http://localhost:9000/internal-sink");
    const submitBtn = page.getByRole("button", { name: /Register Subscription/i });
    await submitBtn.click();

    // Verify SSRF block message
    await expect(page.getByText(/Invalid or unsafe URL: Addresses pointing to localhost/i)).toBeVisible();
  });

  test("checks integrations and pings connectors", async ({ page }) => {
    await page.goto("/developer/integrations");

    await expect(page.getByText("External Integrations & Connectors")).toBeVisible();
    await expect(page.getByText("Amazon S3 Document Lake")).toBeVisible();
    await expect(page.getByText("Relational Knowledge DB")).toBeVisible();
    await expect(page.getByText("Vector Search Cluster")).toBeVisible();

    const pingButtons = page.getByRole("button", { name: /Test Ping/i });
    await expect(pingButtons.first()).toBeVisible();
    await pingButtons.first().click();
  });
});
