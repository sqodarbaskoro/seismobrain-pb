/**
 * @file auth.ts
 * @description Playwright helpers to register/login against real API
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.2
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { APIRequestContext, Page } from "@playwright/test";

const API = `http://127.0.0.1:${process.env.E2E_API_PORT || "18080"}`;
const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL || "admin@example.com";
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || "e2e-admin-pass-12";

let seq = 0;

async function applySession(
  page: Page,
  body: { access_token: string; csrf_token: string },
): Promise<void> {
  await page.addInitScript(
    ({ access, csrf }) => {
      sessionStorage.setItem("sb_access_token", access);
      sessionStorage.setItem("sb_csrf_token", csrf);
    },
    { access: body.access_token, csrf: body.csrf_token },
  );
}

/**
 * Logs the page in as the seeded admin and returns the bearer token, so callers that
 * also need to call the API directly (e.g. to verify server-side state) act as the
 * exact same principal the page did — collection ACLs are per-user, not per-role.
 */
export async function loginAsAdmin(
  page: Page,
  request: APIRequestContext,
): Promise<{ access_token: string; csrf_token: string }> {
  const login = await request.post(`${API}/auth/token`, {
    data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
  });
  if (!login.ok()) {
    throw new Error(`admin login failed: ${login.status()} ${await login.text()}`);
  }
  const body = (await login.json()) as { access_token: string; csrf_token: string };
  await applySession(page, body);
  return body;
}

export async function registerAndLogin(
  page: Page,
  request: APIRequestContext,
): Promise<{ email: string; password: string }> {
  seq += 1;
  const email = `e2e-${Date.now()}-${seq}@example.com`;
  const password = "long-enough-pass";
  const name = `E2E ${seq}`;
  const reg = await request.post(`${API}/auth/register`, {
    data: { email, password, name },
  });
  if (!reg.ok()) {
    throw new Error(`register failed: ${reg.status()} ${await reg.text()}`);
  }
  const login = await request.post(`${API}/auth/token`, {
    data: { email, password },
  });
  if (!login.ok()) {
    throw new Error(`login failed: ${login.status()} ${await login.text()}`);
  }
  await applySession(
    page,
    (await login.json()) as { access_token: string; csrf_token: string },
  );
  return { email, password };
}
