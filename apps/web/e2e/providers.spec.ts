/**
 * @file providers.spec.ts
 * @description Admin can edit and remove LLM providers from settings
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

const api = `http://127.0.0.1:${process.env.E2E_API_PORT || "18080"}`;

test("admin can edit and remove a provider", async ({ page, request }) => {
  const auth = await loginAsAdmin(page, request);
  const authHeaders = { Authorization: `Bearer ${auth.access_token}` };

  const created = await request.post(`${api}/admin/providers`, {
    headers: authHeaders,
    data: {
      kind: "ollama_vllm",
      name: "E2E Ollama",
      base_url: "http://127.0.0.1:11434/v1",
      models: ["llama3.2"],
      api_key: "ollama",
      locality: "local",
    },
  });
  expect(created.ok()).toBeTruthy();
  const provider = (await created.json()) as { id: string };

  await page.route(`**/admin/providers/${provider.id}/test`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true }),
    });
  });

  await page.goto("/settings/providers");
  await expect(page.getByTestId("admin-providers")).toBeVisible();
  await expect(page.getByText("E2E Ollama")).toBeVisible();

  await page.getByTestId(`provider-edit-${provider.id}`).click();
  await expect(page.getByTestId("provider-edit-dialog")).toBeVisible();
  await page.getByLabel("Name").fill("E2E Ollama renamed");
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("E2E Ollama renamed")).toBeVisible();

  await page.getByTestId(`provider-remove-${provider.id}`).click();
  await expect(page.getByTestId("provider-remove-dialog")).toBeVisible();
  await page.getByTestId("provider-remove-confirm").click();
  await expect(page.getByText("E2E Ollama renamed")).toHaveCount(0);

  const listed = await request.get(`${api}/admin/providers`, { headers: authHeaders });
  expect(listed.ok()).toBeTruthy();
  const body = (await listed.json()) as { providers: { id: string }[] };
  expect(body.providers.some((p) => p.id === provider.id)).toBeFalsy();
});
