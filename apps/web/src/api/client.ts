/**
 * @file client.ts
 * @description Authenticated fetch wrapper with 401 → refresh → re-login
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import {
  getAccessToken,
  getCsrfToken,
  useSession,
  type AuthUser,
} from "@/auth/session";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function parseDetail(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
    if (body.detail != null) return JSON.stringify(body.detail);
  } catch {
    // ignore
  }
  return res.statusText || `HTTP ${res.status}`;
}

async function tryRefresh(): Promise<boolean> {
  const csrf = getCsrfToken();
  if (!csrf) return false;
  const res = await fetch("/auth/refresh", {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRF-Token": csrf },
  });
  if (!res.ok) return false;
  const body = (await res.json()) as { access_token: string; csrf_token: string };
  useSession.getState().setTokens(body.access_token, body.csrf_token);
  return true;
}

export type ApiFetchOptions = RequestInit & { skipAuth?: boolean };

export async function apiFetch(
  path: string,
  options: ApiFetchOptions = {},
): Promise<Response> {
  const { skipAuth, headers: initHeaders, ...rest } = options;
  const headers = new Headers(initHeaders);
  if (!skipAuth) {
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  if (rest.body && !(rest.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let res = await fetch(path, { ...rest, headers, credentials: "include" });
  if (res.status === 401 && !skipAuth && !path.startsWith("/auth/")) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      const retryHeaders = new Headers(initHeaders);
      const token = getAccessToken();
      if (token) retryHeaders.set("Authorization", `Bearer ${token}`);
      if (
        rest.body &&
        !(rest.body instanceof FormData) &&
        !retryHeaders.has("Content-Type")
      ) {
        retryHeaders.set("Content-Type", "application/json");
      }
      res = await fetch(path, {
        ...rest,
        headers: retryHeaders,
        credentials: "include",
      });
    }
    if (res.status === 401) {
      useSession.getState().clear();
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.assign(`/login?next=${encodeURIComponent(window.location.pathname)}`);
      }
    }
  }
  return res;
}

export async function apiJson<T>(path: string, options?: ApiFetchOptions): Promise<T> {
  const res = await apiFetch(path, options);
  if (!res.ok) throw new ApiError(res.status, await parseDetail(res));
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export async function fetchAuthStatus(): Promise<{
  has_users: boolean;
  registration_mode: "approval" | "closed" | "open";
}> {
  return apiJson("/auth/status", { skipAuth: true });
}

export async function registerUser(input: {
  email: string;
  password: string;
  name: string;
}): Promise<{
  id: string;
  email: string;
  status: string;
  system_role: string;
}> {
  return apiJson("/auth/register", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify(input),
  });
}

export async function login(email: string, password: string): Promise<void> {
  const body = await apiJson<{ access_token: string; csrf_token: string }>(
    "/auth/token",
    {
      method: "POST",
      skipAuth: true,
      body: JSON.stringify({ email, password }),
    },
  );
  useSession.getState().setTokens(body.access_token, body.csrf_token);
  const me = await apiJson<AuthUser>("/auth/me");
  useSession.getState().setUser(me);
}

export async function loadMe(): Promise<AuthUser> {
  const me = await apiJson<AuthUser>("/auth/me");
  useSession.getState().setUser(me);
  return me;
}
