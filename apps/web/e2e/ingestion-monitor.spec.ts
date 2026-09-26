import { expect, test } from "@playwright/test";
import { loginAsAdmin } from "./auth";

const API = `http://127.0.0.1:${process.env.E2E_API_PORT || "18080"}`;

test("ingestion monitor shows upload, failure, quarantine, release, and actual retry", async ({ page, request }) => {
  const admin = await loginAsAdmin(page, request);
  const headers = { Authorization: `Bearer ${admin.access_token}` };
  const ws = await request.post(`${API}/admin/workspaces`, { headers, data: { name: `Monitor-${Date.now()}` } });
  expect(ws.ok()).toBeTruthy();
  const workspace = await ws.json();
  const col = await request.post(`${API}/admin/workspaces/${workspace.id}/collections`, { headers, data: { name: "monitor" } });
  expect(col.ok()).toBeTruthy();
  const collection = await col.json();
  const filename = `monitor-recoverable-${Date.now()}.md`;
  const upload = await request.post(`${API}/api/v1/collections/${collection.id}/documents`, {
    headers,
    multipart: { file: { name: filename, mimeType: "text/markdown", buffer: Buffer.from("# Guide\n\nThe torque is 40 Nm.") } },
  });
  expect(upload.ok()).toBeTruthy();
  const { job_id } = await upload.json();
  await page.goto("/system/ingestion");
  await page.getByLabel("Search documents").fill(filename);
  const row = page.getByTestId("ingestion-job-row").filter({ hasText: filename });
  await expect(row).toContainText("dead letter", { timeout: 20_000 });
  await expect(row).toContainText("PARSED");
  await row.getByRole("button", { name: "Details" }).click();
  await expect(page.getByRole("dialog")).toContainText("failed");
  await page.getByRole("button", { name: "Close", exact: true }).click();

  await row.getByRole("button", { name: "Quarantine", exact: true }).click();
  await page.getByLabel("Reason").fill("Inspect source before retry");
  await page.getByRole("button", { name: "Quarantine job" }).click();
  await expect(row).toContainText("quarantined");
  const quarantined = await request.get(`${API}/api/v1/admin/ingestion/jobs/${job_id}`, { headers });
  expect((await quarantined.json()).status).toBe("quarantined");

  // Releasing revalidates the source; the unresolved fault fails again.
  await row.getByRole("button", { name: "Release and retry" }).click();
  await expect(row).toContainText("dead letter", { timeout: 20_000 });
  const restore = await request.post(`${API}/_test/ingestion/${job_id}/restore`, { headers });
  expect(restore.ok()).toBeTruthy();
  await row.getByRole("button", { name: "Retry job" }).click();
  await expect(row).toContainText("succeeded", { timeout: 20_000 });
  await row.getByRole("button", { name: "Details" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toContainText("CHUNKED");
  await expect(dialog).toContainText("INDEXED");
  await expect(dialog).not.toContainText("EMBEDDED");
  const detail = await request.get(`${API}/api/v1/admin/ingestion/jobs/${job_id}`, { headers });
  const result = await detail.json();
  expect(result.attempts).toBe(7);
  expect(result.events.some((event: { status: string }) => event.status === "retry")).toBeTruthy();

  // Responsive table stays within its own scrolling region.
  await page.getByRole("button", { name: "Close", exact: true }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(row).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
});
