/**
 * @file DocumentsPage.test.tsx
 * @description Multi-file upload behavior on the Documents collection browser
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-18
 * @modified 2026-09-18
 * @version 0.1.1
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DocumentsPage } from "@/pages/DocumentsPage";

vi.mock("@/auth/session", () => ({
  useSession: (selector: (s: { user: { system_role: string } }) => unknown) =>
    selector({ user: { system_role: "system_admin" } }),
}));

vi.mock("@/api/services/documents", () => ({
  browseDocuments: vi.fn(async () => ({ documents: [] })),
  uploadDocument: vi.fn(async (_collectionId: string, file: File) => ({
    document_id: `doc-${file.name}`,
    job_id: `job-${file.name}`,
    object_key: file.name,
  })),
  getIngestJobStatus: vi.fn(async () => ({
    id: "job", stage: "READY", status: "succeeded" as const, error: null,
  })),
  loadSampleDocuments: vi.fn(),
  previewDocument: vi.fn(),
  downloadDocument: vi.fn(),
  bulkAction: vi.fn(),
  updateDocumentMetadata: vi.fn(),
}));

vi.mock("@/api/services/workspaces", () => ({
  listWorkspaces: vi.fn(async () => ({ workspaces: [] })),
  listMyWorkspaces: vi.fn(async () => ({
    workspaces: [{ id: "ws-1", name: "Workspace 1", collections: [{ id: "col-1", name: "Collection 1" }] }],
  })),
  createCollection: vi.fn(),
}));

vi.mock("@/components/ui/sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

import { uploadDocument } from "@/api/services/documents";
import { toast } from "@/components/ui/sonner";

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <DocumentsPage />
    </QueryClientProvider>,
  );
}

/** jsdom does not populate input.files from change events; assign explicitly. */
function assignFiles(input: HTMLInputElement, files: File[]) {
  Object.defineProperty(input, "files", {
    configurable: true,
    value: files,
  });
}

describe("DocumentsPage multi-file upload", () => {
  beforeEach(() => {
    vi.mocked(uploadDocument).mockReset();
    vi.mocked(uploadDocument).mockImplementation(async (_collectionId: string, file: File) => ({
      document_id: `doc-${file.name}`,
      job_id: `job-${file.name}`,
      object_key: file.name,
    }));
    vi.mocked(toast.success).mockClear();
  });

  it("allows selecting multiple files and uploads each sequentially", async () => {
    renderPage();
    await screen.findByTestId("documents-page");
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Upload" })).not.toBeDisabled();
    });

    const input = document.querySelector("#file") as HTMLInputElement;
    expect(input.multiple).toBe(true);

    const files = [
      new File(["alpha"], "alpha.md", { type: "text/markdown" }),
      new File(["beta"], "beta.md", { type: "text/markdown" }),
    ];
    assignFiles(input, files);
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(uploadDocument).toHaveBeenCalledTimes(2);
    });
    expect(uploadDocument).toHaveBeenNthCalledWith(1, "col-1", files[0]);
    expect(uploadDocument).toHaveBeenNthCalledWith(2, "col-1", files[1]);
    await waitFor(() => {
      expect(toast.success).toHaveBeenCalledWith(
        "Uploading 2 files. They'll appear below once processed.",
      );
    });
  });

  it("continues after a partial failure and surfaces failed filenames", async () => {
    vi.mocked(uploadDocument)
      .mockResolvedValueOnce({
        document_id: "doc-ok",
        job_id: "job-ok",
        object_key: "ok.md",
      })
      .mockRejectedValueOnce(new Error("boom"));

    renderPage();
    await screen.findByTestId("documents-page");
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Upload" })).not.toBeDisabled();
    });

    const input = document.querySelector("#file") as HTMLInputElement;
    const files = [
      new File(["ok"], "ok.md", { type: "text/markdown" }),
      new File(["bad"], "bad.md", { type: "text/markdown" }),
    ];
    assignFiles(input, files);
    fireEvent.submit(input.closest("form")!);

    await waitFor(() => {
      expect(uploadDocument).toHaveBeenCalledTimes(2);
    });
    expect(await screen.findByText(/1 of 2 failed: bad\.md: upload failed/)).toBeInTheDocument();
    expect(toast.success).toHaveBeenCalledWith("Uploaded 1 of 2 files.");
  });
});
