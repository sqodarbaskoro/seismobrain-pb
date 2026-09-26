/**
 * @file teams.spec.ts
 * @description Create a team, add a member, grant collection access, see it merged into ACL view
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

test("creates a team, adds a member, grants collection access, sees it on Workspaces", async ({
  page,
  request,
}) => {
  const admin = await loginAsAdmin(page, request);
  const authHeaders = { Authorization: `Bearer ${admin.access_token}` };

  const workspaceName = `Teams-e2e-${Date.now()}`;
  const ws = await request.post(`${API}/admin/workspaces`, {
    headers: authHeaders,
    data: { name: workspaceName },
  });
  const { id: workspaceId } = (await ws.json()) as { id: string };
  const col = await request.post(`${API}/admin/workspaces/${workspaceId}/collections`, {
    headers: authHeaders,
    data: { name: "ops-docs" },
  });
  const { id: collectionId } = (await col.json()) as { id: string };

  const teamName = `Engineers-${Date.now()}`;
  await page.goto("/people/teams");
  await expect(page.getByTestId("teams-page")).toBeVisible();
  await page.getByLabel("New team name").fill(teamName);
  await page.getByRole("button", { name: "Add" }).click();

  await expect(page.getByTestId("team-detail")).toBeVisible();
  await page.getByLabel("User id to add").fill("engineer-1");
  await page.getByRole("button", { name: "Add member" }).click();
  await expect(page.getByText("engineer-1")).toBeVisible();

  await page.getByLabel("Collection or document id").fill(collectionId);
  await page.getByRole("button", { name: "Grant" }).click();
  await expect(page.getByText(/Granted read on collection/)).toBeVisible();

  await page.goto("/settings/workspaces");
  await page.getByRole("combobox", { name: "Workspace" }).click();
  await page.getByRole("option", { name: workspaceName }).click();
  await page.getByRole("combobox", { name: "Collection" }).click();
  await page.getByRole("option", { name: "ops-docs" }).click();

  await expect(page.getByText(teamName)).toBeVisible();
  await expect(page.getByTestId("acl-editor")).toContainText("read");
});
