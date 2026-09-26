/**
 * @file nav.spec.ts
 * @description App shell nav discoverability and role gating for admin sections
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.3.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { expect, test, type Page } from "@playwright/test";
import { loginAsAdmin, registerAndLogin } from "./auth";

/** Below md the nav lives behind a hamburger; open it if collapsed. No-op on desktop viewports. */
async function ensureNavOpen(page: Page) {
  await expect(page.getByTestId("app-shell")).toBeVisible();
  const toggle = page.getByRole("button", { name: "Open menu" });
  if (await toggle.isVisible()) await toggle.click();
}

test("app shell nav discoverability", async ({ page, request }) => {
  await loginAsAdmin(page, request);
  await page.goto("/chat");

  const shell = page.getByTestId("app-shell");
  await expect(shell).toBeVisible();
  await ensureNavOpen(page);
  await expect(page.getByTestId("primary-nav")).toBeVisible();
  await expect(page.getByTestId("admin-nav")).toBeVisible();
  await expect(page.getByTestId("admin-nav-people")).toBeVisible();
  await expect(page.getByTestId("admin-nav-settings")).toBeVisible();
  await expect(page.getByTestId("admin-nav-system")).toBeVisible();

  await page.getByRole("navigation", { name: "Primary" }).getByRole("link", { name: "Documents" }).click();
  await expect(page).toHaveURL(/\/library/);
  await expect(page.getByTestId("documents-page")).toBeVisible();

  await page.getByRole("link", { name: "Users" }).click();
  await expect(page).toHaveURL(/\/people\/users/);
  await expect(page.getByTestId("admin-users")).toBeVisible();

  await page.getByRole("link", { name: "Providers" }).click();
  await expect(page.getByTestId("admin-providers")).toBeVisible();

  await page.getByRole("link", { name: "Workspaces" }).click();
  await expect(page.getByTestId("admin-workspaces")).toBeVisible();

  await page.getByRole("link", { name: "Ingestion" }).click();
  await expect(page.getByTestId("admin-ingestion")).toBeVisible();

  await page.getByRole("link", { name: "Chat" }).click();
  await expect(page.getByTestId("chat-page")).toBeVisible();
});

test("non-admin members neither see nor can reach admin sections", async ({ page, request }) => {
  await registerAndLogin(page, request);
  await page.goto("/chat");

  await ensureNavOpen(page);
  await expect(page.getByTestId("primary-nav")).toBeVisible();
  await expect(page.getByTestId("admin-nav")).toHaveCount(0);

  await page.goto("/people/users");
  await expect(page.getByTestId("access-denied")).toBeVisible();
  await expect(page.getByTestId("admin-users")).toHaveCount(0);
});
