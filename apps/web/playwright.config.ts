/**
 * @file playwright.config.ts
 * @description Playwright e2e config for SeismoBrain web
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-16
 * @modified 2026-09-17
 * @version 0.2.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, devices } from "@playwright/test";

const apiPort = process.env.E2E_API_PORT || "18080";
const apiUrl = `http://127.0.0.1:${apiPort}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "on-first-retry",
  },
  webServer: [
    {
      command: `E2E_API_PORT=${apiPort} node ../../scripts/e2e-api.mjs`,
      cwd: path.dirname(fileURLToPath(import.meta.url)),
      url: `${apiUrl}/health`,
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5173",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        VITE_API_PROXY: apiUrl,
      },
    },
  ],
  projects: [
    {
      name: "chromium",
      testIgnore: ["**/mobile.spec.ts"],
      use: { ...devices["Desktop Chrome"] },
    },
    // Full multi-step desktop workflows stay chromium-only; mobile only re-runs the pieces
    // that actually change shape at a phone width (see e2e/mobile.spec.ts).
    {
      name: "mobile",
      testMatch: ["**/nav.spec.ts", "**/mobile.spec.ts"],
      use: { ...devices["Pixel 5"] },
    },
  ],
});
