/**
 * @file AdminProvidersPage.test.tsx
 * @description Edit and remove actions on the admin providers settings page
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { AdminProvidersPage } from "@/pages/AdminProvidersPage";

const provider = {
  id: "prov-1",
  name: "OpenRouter",
  kind: "openai_compatible",
  base_url: "https://openrouter.ai/api/v1",
  locality: "external",
  models: ["openai/gpt-4o-mini"],
};

vi.mock("@/api/services/providers", () => ({
  listProviders: vi.fn(async () => ({ providers: [provider] })),
  createProvider: vi.fn(async (_body: { name: string }) => provider),
  updateProvider: vi.fn(async (_id: string, body: { name: string }) => ({
    ...provider,
    name: body.name,
  })),
  deleteProvider: vi.fn(async () => undefined),
  testProvider: vi.fn(async () => ({ ok: true })),
}));

import {
  createProvider,
  deleteProvider,
  listProviders,
  updateProvider,
} from "@/api/services/providers";

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <MemoryRouter>
      <QueryClientProvider client={client}>
        <AdminProvidersPage />
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

describe("AdminProvidersPage edit/remove", () => {
  beforeEach(() => {
    vi.mocked(listProviders).mockResolvedValue({ providers: [provider] });
    vi.mocked(updateProvider).mockClear();
    vi.mocked(createProvider).mockClear();
    vi.mocked(deleteProvider).mockClear();
  });

  it("shows Edit and Remove and can save an edit", async () => {
    renderPage();
    await screen.findByText("OpenRouter");
    expect(screen.getByTestId("provider-edit-prov-1")).toBeInTheDocument();
    expect(screen.getByTestId("provider-remove-prov-1")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("provider-edit-prov-1"));
    const nameInput = await screen.findByLabelText("Name");
    fireEvent.change(nameInput, { target: { value: "OpenRouter renamed" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(updateProvider).toHaveBeenCalledWith(
        "prov-1",
        expect.objectContaining({ name: "OpenRouter renamed" }),
      );
    });
  });

  it("confirms and removes a provider", async () => {
    renderPage();
    await screen.findByText("OpenRouter");
    fireEvent.click(screen.getByTestId("provider-remove-prov-1"));
    await screen.findByTestId("provider-remove-dialog");
    fireEvent.click(screen.getByTestId("provider-remove-confirm"));
    await waitFor(() => {
      expect(deleteProvider).toHaveBeenCalledWith("prov-1");
    });
  });

  it("offers direct add and Guided Setup when no providers exist", async () => {
    vi.mocked(listProviders).mockResolvedValueOnce({ providers: [] });
    renderPage();

    expect(await screen.findByRole("button", { name: "Add provider" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Use Guided Setup" })).toBeInTheDocument();
  });

  it("creates and tests a provider from the add dialog", async () => {
    vi.mocked(listProviders).mockResolvedValueOnce({ providers: [] });
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Add provider" }));

    expect(await screen.findByTestId("provider-add-dialog")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("API key"), { target: { value: "secret" } });
    fireEvent.click(screen.getByRole("button", { name: "Add and test" }));

    await waitFor(() => {
      expect(createProvider).toHaveBeenCalledWith(expect.objectContaining({
        kind: "openai_compatible",
        name: "OpenAI-compatible / OpenRouter",
        api_key: "secret",
      }));
    });
  });
});
