/**
 * @file login.spec.ts
 * @description Playwright login / first-admin smoke against real API
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

test("login smoke via UI", async ({ page }) => {
  const email = `ui-login-${Date.now()}@example.com`;
  const password = "long-enough-pass";

  await page.goto("/register");
  await expect(page.getByTestId("register-page")).toBeVisible();
  await page.getByLabel("Name").fill("UI Admin");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel(/Password/).fill(password);
  await page.getByRole("button", { name: /Create admin|Register/ }).click();
  await expect(page).toHaveURL(/\/(onboarding|chat)/);

  await page.goto("/login");
  await expect(page.getByTestId("login-page")).toBeVisible();
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/onboarding/);
});
