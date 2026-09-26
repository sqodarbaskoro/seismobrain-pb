/**
 * @file quarantine.spec.ts
 * @description Files-needing-review inbox: empty state, then list + release
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
import { loginAsAdmin } from "./auth";

const API = `http://127.0.0.1:${process.env.E2E_API_PORT || "18080"}`;

test("shows an empty state, then lists and releases a flagged file", async ({
  page,
  request,
}) => {
  const admin = await loginAsAdmin(page, request);
  const authHeaders = { Authorization: `Bearer ${admin.access_token}` };

  await page.goto("/settings/quarantine");
  await expect(page.getByTestId("quarantine-page")).toBeVisible();
  await expect(page.getByText("Nothing is waiting for review right now.")).toBeVisible();

  await request.post(`${API}/api/v1/quarantine`, {
    headers: authHeaders,
    data: { filename: "invoice.exe", reason: "unexpected executable" },
  });

  await page.reload();
  const row = page.getByTestId("quarantine-row");
  await expect(row).toContainText("invoice.exe");
  await expect(row).toContainText("unexpected executable");

  await row.getByRole("button", { name: "Release" }).click();
  await expect(page.getByText("Nothing is waiting for review right now.")).toBeVisible();
});
