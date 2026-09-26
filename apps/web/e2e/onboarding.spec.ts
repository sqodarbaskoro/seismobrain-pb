/**
 * @file onboarding.spec.ts
 * @description Guided setup wizard: provider → workspace/collection → sample docs → chat
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.2.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { expect, test } from "@playwright/test";
import { loginAsAdmin } from "./auth";

test("guided setup wizard end to end, with sample documents", async ({ page, request }) => {
  const admin = await loginAsAdmin(page, request);
  const authHeaders = { Authorization: `Bearer ${admin.access_token}` };

  // Stub provider connection test so CI does not call OpenRouter.
  await page.route("**/admin/providers/*/test", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true }),
    });
  });

  await page.goto("/onboarding");
  await expect(page.getByTestId("onboarding-wizard")).toBeVisible();
  await expect(page.getByText("Step 1 of 5: Welcome")).toBeVisible();
  await page.getByRole("button", { name: "Get started" }).click();

  await expect(page.getByText("Step 2 of 5")).toBeVisible();
  await page.getByRole("combobox", { name: "LLM provider" }).click();
  await page.getByRole("option", { name: "Ollama / vLLM (runs on this machine)" }).click();
  await page.getByLabel("API key").fill("local-key");
  await page.getByRole("button", { name: "Test connection & continue" }).click();
  await expect(page.getByTestId("provider-test-ok")).toBeVisible();
  await page.getByRole("button", { name: "Next" }).click();

  await expect(page.getByText("Step 3 of 5")).toBeVisible();
  await page.getByLabel("Workspace name").fill("Pilot");
  await page.getByLabel("First collection").fill("ops");
  await page.getByRole("button", { name: "Next" }).click();

  await expect(page.getByText("Step 4 of 5")).toBeVisible();
  await page.getByRole("button", { name: "Load sample documents" }).click();
  await expect(page.getByText("Sample documents added")).toBeVisible();
  await page.getByRole("button", { name: "Next" }).click();

  await expect(page.getByText("Step 5 of 5")).toBeVisible();
  await expect(
    page.getByText("What's the procedure for inspecting the CP-100 pump?"),
  ).toBeVisible();
  await page.getByTestId("onboarding-finish").click();

  await expect(page).toHaveURL(/\/chat\?q=/);
  await expect(page.getByLabel("Message")).toHaveValue(
    "What's the procedure for inspecting the CP-100 pump?",
  );

  const api = `http://127.0.0.1:${process.env.E2E_API_PORT || "18080"}`;
  const providers = await request.get(`${api}/admin/providers`, { headers: authHeaders });
  expect(providers.ok()).toBeTruthy();
  const providerBody = (await providers.json()) as { providers: { kind: string }[] };
  expect(providerBody.providers.some((p) => p.kind === "ollama_vllm")).toBeTruthy();

  const workspaces = await request.get(`${api}/admin/workspaces`, { headers: authHeaders });
  const wsBody = (await workspaces.json()) as { workspaces: { id: string; name: string }[] };
  const pilot = wsBody.workspaces.find((w) => w.name === "Pilot");
  expect(pilot).toBeTruthy();

  const collections = await request.get(`${api}/admin/workspaces/${pilot!.id}/collections`, {
    headers: authHeaders,
  });
  const colBody = (await collections.json()) as { collections: { id: string; name: string }[] };
  const ops = colBody.collections.find((c) => c.name === "ops");
  expect(ops).toBeTruthy();

  // Same principal that ran the wizard: collection reads are per-user grants, not
  // per-role, so an arbitrary "system admin" header wouldn't be entitled to read this
  // collection even though it created it.
  const documents = await request.get(`${api}/api/v1/collections/${ops!.id}/documents`, {
    headers: authHeaders,
  });
  const docsBody = (await documents.json()) as { documents: unknown[] };
  expect(docsBody.documents.length).toBeGreaterThan(0);
});
