import { describe, expect, it } from "vitest";
import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

describe("Design tokens", () => {
  const candidatePaths = [
    resolve(__dirname, "../../src/styles/tokens.css"),
    resolve(process.cwd(), "src/styles/tokens.css"),
    resolve(process.cwd(), "web/src/styles/tokens.css"),
  ];

  const targetPath = candidatePaths.find((p) => existsSync(p)) || candidatePaths[0];
  const css = readFileSync(targetPath, "utf8");

  const requiredTokens = [
    "--background",
    "--surface",
    "--foreground",
    "--muted",
    "--border",
    "--primary",
    "--success",
    "--warning",
    "--danger",
    "--space-1",
    "--space-4",
    "--radius-md",
  ];

  it.each(requiredTokens)("defines %s", (token) => {
    expect(css).toContain(token);
  });
});
