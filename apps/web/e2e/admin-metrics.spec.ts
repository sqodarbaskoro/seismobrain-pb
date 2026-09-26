/**
 * @file admin-metrics.spec.ts
 * @description Admin metrics dashboard: usage, latency, refusals, feedback (FR-ADM-08)
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-26
 * @modified 2026-09-26
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { expect, test } from "@playwright/test";
import { loginAsAdmin, registerAndLogin } from "./auth";

test("admin sees usage metrics reflecting a chat message", async ({ page, request }) => {
  await loginAsAdmin(page, request);
  await page.goto("/chat");
  await page.getByTestId("new-chat-button").click();
  await page.getByLabel("Message").fill("What is the calibration procedure?");
  await page.getByRole("button", { name: "Send", exact: true }).click();
  await expect(page.getByTestId("message-list")).not.toContainText("Ask a question about");

  await page.goto("/system/metrics");
  await expect(page.getByTestId("admin-metrics")).toBeVisible();
  const tiles = page.getByTestId("metrics-stat-tiles");
  await expect(tiles.getByText("Chat requests")).toBeVisible();
  await expect(tiles.getByText("p95 latency")).toBeVisible();
  await expect(tiles.getByText("Refusal rate")).toBeVisible();
  await expect(tiles.getByText("Found helpful")).toBeVisible();
});

test("non-admin cannot reach metrics", async ({ page, request }) => {
  await registerAndLogin(page, request);
  await page.goto("/system/metrics");
  await expect(page.getByTestId("access-denied")).toBeVisible();
  await expect(page.getByTestId("admin-metrics")).toHaveCount(0);
});
