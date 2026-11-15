import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  testMatch: "**/*.spec.ts",
  timeout: 30000,
  expect: {
    timeout: 5000,
  },
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || process.env.BASE_URL || "http://127.0.0.1:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "e2e",
      testDir: "./tests/e2e",
      testMatch: "**/*.spec.ts",
    },
    {
      name: "navigation",
      testDir: "./tests/e2e/navigation",
      testMatch: "**/*.spec.ts",
    },
    {
      name: "interaction",
      testDir: "./tests/interaction",
      testMatch: "**/*.spec.ts",
    },
    {
      name: "integration",
      testDir: "./tests/integration",
      testMatch: "**/*.spec.ts",
    },
    {
      name: "visual",
      testDir: "./tests/visual",
      testMatch: "**/*.spec.ts",
    },
    {
      name: "accessibility",
      testDir: "./tests/accessibility",
      testMatch: "**/*.spec.ts",
    },
    {
      name: "responsive",
      testDir: "./tests/responsive",
      testMatch: "**/*.spec.ts",
    },
  ],
});
