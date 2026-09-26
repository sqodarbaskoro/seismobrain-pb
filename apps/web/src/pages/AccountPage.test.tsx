/**
 * @file AccountPage.test.tsx
 * @description API key create/list/delete and scope/expiry UI (T04.5, FR-AUTH-07)
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-19
 * @modified 2026-09-19
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AccountPage } from "@/pages/AccountPage";

const token = {
  id: "tok_1",
  name: "ci",
  scopes: ["read"],
  expires_at: 4102444800,
  kind: "personal" as const,
  revoked: false,
};

vi.mock("@/api/services/account", async () => {
  const actual = await vi.importActual<typeof import("@/api/services/account")>(
    "@/api/services/account",
  );
  return {
    ...actual,
    listSessions: vi.fn(async () => ({ sessions: [] })),
    listApiTokens: vi.fn(async () => ({ tokens: [] as (typeof token)[] })),
    issueApiToken: vi.fn(async () => ({
      id: "tok_1",
      token: "sbpat_test-secret",
      scopes: ["read"],
      expires_at: 4102444800,
    })),
    deleteApiToken: vi.fn(async () => ({ deleted: true })),
  };
});

import { issueApiToken, listApiTokens, deleteApiToken } from "@/api/services/account";

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <AccountPage />
    </QueryClientProvider>,
  );
}

describe("AccountPage API keys", () => {
  beforeEach(() => {
    vi.mocked(listApiTokens).mockResolvedValue({ tokens: [] });
    vi.mocked(issueApiToken).mockClear();
    vi.mocked(deleteApiToken).mockClear();
  });

  it("creates a key with the fixed read scope and 90-day ttl, reveals the secret once", async () => {
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: "New key" }));
    fireEvent.change(await screen.findByLabelText("Name"), {
      target: { value: "reporting script" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create" }));

    await waitFor(() => {
      expect(issueApiToken).toHaveBeenCalledWith({
        name: "reporting script",
        scopes: ["read"],
        ttl_seconds: 60 * 60 * 24 * 90,
      });
    });
    expect(await screen.findByText("sbpat_test-secret")).toBeInTheDocument();
  });

  it("cannot free-type a scope — only the fixed, disabled Read permission is offered", async () => {
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: "New key" }));
    await screen.findByLabelText("Name");
    expect(screen.queryByLabelText(/scopes/i)).not.toBeInTheDocument();
    const checkbox = screen.getByRole("checkbox") as HTMLInputElement;
    expect(checkbox.checked).toBe(true);
    expect(checkbox.disabled).toBe(true);
  });

  it("lists existing keys and deletes one", async () => {
    vi.mocked(listApiTokens).mockResolvedValue({ tokens: [token] });
    renderPage();
    await screen.findByText("ci");
    expect(screen.getByText("read")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    await waitFor(() => {
      expect(deleteApiToken).toHaveBeenCalledWith("tok_1");
    });
  });
});
