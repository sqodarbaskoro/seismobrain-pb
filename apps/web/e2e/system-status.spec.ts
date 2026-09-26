/**
 * @file system-status.spec.ts
 * @description "Is everything running?" panel — health, readiness, config for admins
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { expect, test } from "@playwright/test";
import { loginAsAdmin, registerAndLogin } from "./auth";

test("admin sees component checks and configuration", async ({ page, request }) => {
  await loginAsAdmin(page, request);
  await page.goto("/system/status");

  await expect(page.getByTestId("system-status")).toBeVisible();
  await expect(page.getByText("Everything's running")).toBeVisible();
  await expect(page.getByText("Document database")).toBeVisible();
  await expect(page.getByText("Deployment tier")).toBeVisible();
});

test("non-admin cannot reach system status", async ({ page, request }) => {
  await registerAndLogin(page, request);
  await page.goto("/system/status");
  await expect(page.getByTestId("access-denied")).toBeVisible();
});
