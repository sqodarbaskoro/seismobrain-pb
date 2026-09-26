/**
 * @file glossary.spec.ts
 * @description Dictionary and document-numbering editor persists via the real API
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

test("saves a dictionary term and a numbering pattern", async ({ page, request }) => {
  const admin = await loginAsAdmin(page, request);
  const authHeaders = { Authorization: `Bearer ${admin.access_token}` };

  const ws = await request.post(`${API}/admin/workspaces`, {
    headers: authHeaders,
    data: { name: `Glossary-e2e-${Date.now()}` },
  });
  const { id: workspaceId } = (await ws.json()) as { id: string };

  await page.goto("/settings/glossary");
  await expect(page.getByTestId("glossary-page")).toBeVisible();
  await page.getByRole("combobox", { name: "Workspace" }).click();
  await page.getByRole("option", { name: new RegExp(`Glossary-e2e-`) }).click();

  await page.getByRole("button", { name: "Add term" }).click();
  await page.getByLabel("Term").fill("PPE");
  await page.getByLabel("Expansion").fill("personal protective equipment");
  await page.getByRole("button", { name: "Save dictionary" }).click();
  await expect(page.getByText("Dictionary saved.")).toBeVisible();

  await page.getByRole("tab", { name: "Document numbering" }).click();
  await page.getByRole("button", { name: "Add pattern" }).click();
  await page.getByLabel("Pattern name").fill("flange code");
  await page.getByLabel("Pattern", { exact: true }).fill("P\\d+/\\d+");
  await page.getByRole("button", { name: "Save patterns" }).click();
  await expect(page.getByText("Document numbering patterns saved.")).toBeVisible();

  const got = await request.get(`${API}/api/v1/workspaces/${workspaceId}/glossary`, {
    headers: authHeaders,
  });
  const body = (await got.json()) as {
    glossary: { term: string }[];
    identifier_patterns: { name: string }[];
  };
  expect(body.glossary.some((e) => e.term === "PPE")).toBeTruthy();
  expect(body.identifier_patterns.some((p) => p.name === "flange code")).toBeTruthy();
});
