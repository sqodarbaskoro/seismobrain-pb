/**
 * @file client.test.ts
 * @description Unit tests for authenticated API client
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { afterEach, describe, expect, it, vi } from "vitest";
import { apiFetch, login } from "@/api/client";
import { useSession } from "@/auth/session";

afterEach(() => {
  useSession.getState().clear();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("api client", () => {
  it("login stores tokens and loads /auth/me", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ access_token: "access-1", csrf_token: "csrf-1" }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            id: "u1",
            email: "a@example.com",
            name: "A",
            system_role: "system_admin",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    vi.stubGlobal("fetch", fetchMock);

    await login("a@example.com", "long-enough-pass");

    expect(useSession.getState().accessToken).toBe("access-1");
    expect(useSession.getState().csrfToken).toBe("csrf-1");
    expect(useSession.getState().user?.email).toBe("a@example.com");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("apiFetch attaches bearer and refreshes once on 401", async () => {
    useSession.getState().setTokens("stale", "csrf-old");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response("{}", { status: 401 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ access_token: "fresh", csrf_token: "csrf-new" }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    const res = await apiFetch("/api/v1/conversations");
    expect(res.status).toBe(200);
    expect(useSession.getState().accessToken).toBe("fresh");
    expect(fetchMock).toHaveBeenCalledTimes(3);
    const retryAuth = (fetchMock.mock.calls[2][1] as RequestInit).headers as Headers;
    expect(retryAuth.get("Authorization")).toBe("Bearer fresh");
  });
});
