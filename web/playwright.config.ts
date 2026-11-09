import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 30000,
  expect: {
    timeout: 5000,
  },
  use: {
    baseURL: process.env.BASE_URL || "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  webServer: {
    command: "npm run start -- -p 3000",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: true,
    timeout: 30000,
  },
  projects: [
    {
      name: "e2e",
      testDir: "./tests/e2e",
    },
    {
      name: "accessibility",
      testDir: "./tests/accessibility",
    },
    {
      name: "responsive",
      testDir: "./tests/responsive",
    },
  ],
});
