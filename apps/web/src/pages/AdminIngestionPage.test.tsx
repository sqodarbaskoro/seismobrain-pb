import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, cleanup } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { apiJson } from "@/api/client";
import { AdminIngestionPage } from "./AdminIngestionPage";

vi.mock("@/api/client", () => ({ apiJson: vi.fn(), ApiError: class extends Error {} }));
const job = { id: "job-1", filename: "guide.md", status: "dead_letter", stage: "PARSED", attempts: 3,
  collection_id: "col-1", updated_at: 1000, created_at: 1000, error: "Source file is missing.",
  actions: ["retry", "quarantine"], events: [], history_available: true };
const summary = { queue_depth: 0, running: 0, succeeded: 0, failed: 0, dead_letter: 1, quarantined: 0, stages: {} };
let client: QueryClient;
beforeEach(() => {
  vi.mocked(apiJson).mockReset();
  vi.mocked(apiJson).mockImplementation(async (path, options) => {
    if (options?.method === "POST") return { ...job, status: "pending" };
    if (path.endsWith("/monitor")) return summary;
    if (path.includes("/jobs?")) return { jobs: [job], total: 1, offset: 0, limit: 25 };
    return job;
  });
  client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
});
afterEach(() => { cleanup(); client.clear(); });
function page() { render(<QueryClientProvider client={client}><AdminIngestionPage /></QueryClientProvider>); }

it("shows real job errors and retries the selected job", async () => {
  page();
  await screen.findByText("guide.md");
  expect(screen.getByText("Source file is missing.")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Retry job" }));
  await waitFor(() => expect(apiJson).toHaveBeenCalledWith("/api/v1/admin/ingestion/jobs/job-1/retry", { method: "POST" }));
  expect(await screen.findByText("guide.md queued for processing.")).toBeInTheDocument();
});

it("does not present a failed first load as healthy zeros", async () => {
  vi.mocked(apiJson).mockRejectedValue(new Error("offline"));
  page();
  expect(await screen.findByRole("alert")).toHaveTextContent("Could not refresh");
  expect(screen.getAllByText("Not available")).toHaveLength(6);
});

it("shows stale data explicitly after a previously successful refresh", async () => {
  page();
  await screen.findByText("guide.md");
  vi.mocked(apiJson).mockRejectedValue(new Error("offline"));
  fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("out of date");
  expect(screen.getByText("guide.md")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Retry job" })).toBeDisabled();
});

it("sends filters to the server and displays an empty result", async () => {
  page();
  await screen.findByText("guide.md");
  vi.mocked(apiJson).mockImplementation(async (path) => path.endsWith("/monitor") ? summary : { jobs: [], total: 0 });
  fireEvent.change(screen.getByLabelText("Search documents"), { target: { value: "other" } });
  expect(await screen.findByText(/No ingestion jobs match/)).toBeInTheDocument();
  expect(vi.mocked(apiJson).mock.calls.some(([path]) => path.includes("search=other"))).toBe(true);
});

it("requires a quarantine reason and sends it with the job action", async () => {
  page();
  await screen.findByText("guide.md");
  fireEvent.click(screen.getByRole("button", { name: "Quarantine" }));
  expect(screen.getByRole("button", { name: "Quarantine job" })).toBeDisabled();
  fireEvent.change(screen.getByLabelText("Reason"), { target: { value: "Review source" } });
  fireEvent.click(screen.getByRole("button", { name: "Quarantine job" }));
  await waitFor(() => expect(apiJson).toHaveBeenCalledWith("/api/v1/admin/ingestion/jobs/job-1/quarantine", {
    method: "POST", body: JSON.stringify({ reason: "Review source" }),
  }));
});
