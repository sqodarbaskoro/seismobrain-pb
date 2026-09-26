/**
 * @file account.spec.ts
 * @description Self-service: see your login session, create and revoke an API key
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
import { registerAndLogin } from "./auth";

test("sees the login session and manages an API key", async ({ page, request }) => {
  await registerAndLogin(page, request);

  await page.goto("/account");
  await expect(page.getByTestId("account-page")).toBeVisible();

  // The login itself created a session (a refresh-token family) — it should show up.
  await expect(page.getByRole("heading", { name: "Active sessions" })).toBeVisible();
  const sessionRows = page.locator("table").first().locator("tbody tr");
  await expect(sessionRows).toHaveCount(1);

  await page.getByRole("button", { name: "New key" }).click();
  await page.getByLabel("Name").fill("reporting script");
  await page.getByRole("button", { name: "Create" }).click();

  await expect(page.getByText("Copy your key now")).toBeVisible();
  const revealed = await page.locator("p.font-mono").textContent();
  expect(revealed).toMatch(/^sbpat_/);
  await page.getByRole("button", { name: "Done" }).click();

  await expect(page.getByText("reporting script")).toBeVisible();
  await page.getByRole("button", { name: "Revoke" }).click();
  await expect(page.getByText("Revoked")).toBeVisible();
});
