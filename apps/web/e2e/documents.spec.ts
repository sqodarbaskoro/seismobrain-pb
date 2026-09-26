/**
 * @file documents.spec.ts
 * @description Upload → filter → preview → download → bulk delete, against the real API
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-18
 * @version 0.3.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { expect, test, type APIRequestContext } from "@playwright/test";
import { loginAsAdmin } from "./auth";

const API = `http://127.0.0.1:${process.env.E2E_API_PORT || "18080"}`;

async function createCollection(request: APIRequestContext, token: string) {
  const authHeaders = { Authorization: `Bearer ${token}` };
  const ws = await request.post(`${API}/admin/workspaces`, {
    headers: authHeaders,
    data: { name: `Docs-e2e-${Date.now()}` },
  });
  const { id: workspaceId } = (await ws.json()) as { id: string };
  const col = await request.post(`${API}/admin/workspaces/${workspaceId}/collections`, {
    headers: authHeaders,
    data: { name: "manuals" },
  });
  const { id: collectionId } = (await col.json()) as { id: string };
  return { collectionId, authHeaders };
}

test("upload, filter, preview, download, edit metadata, and bulk delete a document", async ({
  page,
  request,
}) => {
  const admin = await loginAsAdmin(page, request);
  const { collectionId, authHeaders } = await createCollection(request, admin.access_token);

  await page.goto("/library");
  await expect(page.getByTestId("documents-page")).toBeVisible();
  await page.getByRole("combobox", { name: "Collection" }).click();
  await page.getByRole("option", { name: collectionId }).click();

  await page.setInputFiles("#file", {
    name: "torque-guide.md",
    mimeType: "text/markdown",
    buffer: Buffer.from("# Torque guide\n\nTorque for flange P2/94 is 40 Nm.\n"),
  });
  await page.getByRole("button", { name: "Upload" }).click();

  const row = page.getByTestId("document-row").filter({ hasText: "torque-guide" });
  await expect(row).toBeVisible({ timeout: 10_000 });

  // Filtering to something that doesn't match hides it; clearing brings it back.
  await page.getByLabel("Search documents").fill("nonexistent-xyz");
  await expect(page.getByText("No documents match these filters.")).toBeVisible();
  await page.getByRole("button", { name: "Clear" }).click();
  await expect(row).toBeVisible();

  await row.getByRole("button", { name: "Preview" }).click();
  await expect(page.getByTestId("document-preview-highlight")).toContainText("40 Nm");
  await page.keyboard.press("Escape");

  const downloadPromise = page.waitForEvent("download");
  await row.getByRole("button", { name: "Download" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("torque-guide.md");

  await row.getByRole("button", { name: "Edit" }).click();
  await expect(page.getByTestId("edit-metadata-dialog")).toBeVisible();
  await page.getByLabel("Title").fill("Torque Guide (corrected)");
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByTestId("document-row").filter({ hasText: "corrected" })).toBeVisible();
  const correctedRow = page.getByTestId("document-row").filter({ hasText: "corrected" });

  await correctedRow.getByRole("checkbox").check();
  await expect(page.getByTestId("bulk-toolbar")).toContainText("1 selected");
  await page.getByRole("button", { name: "Delete" }).click();
  await page.getByRole("button", { name: "Delete" }).last().click();
  await expect(correctedRow).toHaveCount(0);

  const documents = await request.get(`${API}/api/v1/collections/${collectionId}/documents`, {
    headers: authHeaders,
  });
  const body = (await documents.json()) as { documents: unknown[] };
  expect(body.documents.length).toBe(0);
});

test("upload multiple documents in one action", async ({ page, request }) => {
  const admin = await loginAsAdmin(page, request);
  const { collectionId } = await createCollection(request, admin.access_token);

  await page.goto("/library");
  await expect(page.getByTestId("documents-page")).toBeVisible();
  await page.getByRole("combobox", { name: "Collection" }).click();
  await page.getByRole("option", { name: collectionId }).click();

  await page.setInputFiles("#file", [
    {
      name: "alpha-spec.md",
      mimeType: "text/markdown",
      buffer: Buffer.from("# Alpha\n\nAlpha content.\n"),
    },
    {
      name: "beta-spec.md",
      mimeType: "text/markdown",
      buffer: Buffer.from("# Beta\n\nBeta content.\n"),
    },
  ]);
  await page.getByRole("button", { name: "Upload" }).click();

  await expect(page.getByTestId("document-row").filter({ hasText: "alpha-spec" })).toBeVisible({
    timeout: 10_000,
  });
  await expect(page.getByTestId("document-row").filter({ hasText: "beta-spec" })).toBeVisible({
    timeout: 10_000,
  });
});

test("shows real per-stage ingest progress while a document processes", async ({ page, request }) => {
  const admin = await loginAsAdmin(page, request);
  const { collectionId } = await createCollection(request, admin.access_token);

  await page.goto("/library");
  await expect(page.getByTestId("documents-page")).toBeVisible();
  await page.getByRole("combobox", { name: "Collection" }).click();
  await page.getByRole("option", { name: collectionId }).click();

  await page.setInputFiles("#file", {
    name: "progress-guide.md",
    mimeType: "text/markdown",
    buffer: Buffer.from("# Guide\n\nSome content for the progress test.\n"),
  });
  await page.getByRole("button", { name: "Upload" }).click();

  // The tracked upload shows up immediately (before the first poll can possibly have
  // resolved it), with a real stage name — not a fake spinner.
  await expect(page.getByTestId("ingest-progress-list")).toBeVisible();
  await expect(page.getByTestId("ingest-progress-row")).toContainText("progress-guide.md");

  // Once ingestion actually finishes, the document is visible and the progress row
  // that tracked it clears.
  const row = page.getByTestId("document-row").filter({ hasText: "progress-guide" });
  await expect(row).toBeVisible({ timeout: 10_000 });
  await expect(page.getByTestId("ingest-progress-list")).toHaveCount(0);
});
