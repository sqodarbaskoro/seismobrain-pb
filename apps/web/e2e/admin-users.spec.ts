/**
 * @file admin-users.spec.ts
 * @description Search, role change, and force sign-out on the Users page
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

const API = `http://127.0.0.1:${process.env.E2E_API_PORT || "18080"}`;

test("admin searches, promotes a member, and forces them out", async ({ page, request }) => {
  const admin = await loginAsAdmin(page, request);
  const authHeaders = { Authorization: `Bearer ${admin.access_token}` };

  const memberPage = await page.context().newPage();
  const member = await registerAndLogin(memberPage, request);
  await memberPage.close();

  await page.goto("/people/users");
  await expect(page.getByTestId("admin-users")).toBeVisible();

  await page.getByLabel("Search users").fill(member.email);
  const row = page.getByRole("row", { name: new RegExp(member.email) });
  await expect(row).toBeVisible();

  await row.getByRole("combobox").click();
  await expect(page.getByRole("option", { name: "Admin" })).toBeVisible();
  await page.getByRole("option", { name: "Admin" }).click();
  await expect(row.getByRole("combobox")).toContainText("Admin");

  const listed = await request.get(`${API}/admin/users`, { headers: authHeaders });
  const users = (await listed.json()) as { users: { email: string; system_role: string }[] };
  const promoted = users.users.find((u) => u.email === member.email);
  expect(promoted?.system_role).toBe("system_admin");

  await row.getByRole("button", { name: "Force sign-out" }).click();
  await expect(page.getByText(/Signed out everywhere/)).toBeVisible();
});
