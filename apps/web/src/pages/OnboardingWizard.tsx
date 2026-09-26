/**
 * @file OnboardingWizard.tsx
 * @description Guided setup: account → provider → workspace & collection → documents → try it
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-16
 * @modified 2026-09-17
 * @version 0.3.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, apiFetch, apiJson } from "@/api/client";
import { useSession } from "@/auth/session";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

type ProviderKind = "openai_compatible" | "anthropic" | "gemini" | "ollama_vllm";

const KIND_DEFAULTS: Record<
  ProviderKind,
  { base_url: string; locality: "local" | "external"; model: string; label: string }
> = {
  openai_compatible: {
    base_url: "https://openrouter.ai/api/v1",
    locality: "external",
    model: "openai/gpt-4o-mini",
    label: "OpenAI-compatible / OpenRouter",
  },
  ollama_vllm: {
    base_url: "http://127.0.0.1:11434/v1",
    locality: "local",
    model: "llama3.2",
    label: "Ollama / vLLM (runs on this machine)",
  },
  anthropic: {
    base_url: "https://api.anthropic.com",
    locality: "external",
    model: "claude-3-5-haiku-latest",
    label: "Anthropic",
  },
  gemini: {
    base_url: "https://generativelanguage.googleapis.com",
    locality: "external",
    model: "gemini-2.0-flash",
    label: "Gemini",
  },
};

const STEPS = ["Welcome", "Connect an AI provider", "Workspace & collection", "Add documents", "Try it"];

const SAMPLE_SUGGESTED_QUESTION = "What's the procedure for inspecting the CP-100 pump?";
const GENERIC_SUGGESTED_QUESTION = "What's in my documents?";

export function OnboardingWizard() {
  const navigate = useNavigate();
  const user = useSession((s) => s.user);
  const [step, setStep] = useState(0);

  // Provider
  const [kind, setKind] = useState<ProviderKind>("openai_compatible");
  const [providerName, setProviderName] = useState(KIND_DEFAULTS.openai_compatible.label);
  const [baseUrl, setBaseUrl] = useState(KIND_DEFAULTS.openai_compatible.base_url);
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState(KIND_DEFAULTS.openai_compatible.model);
  const [locality, setLocality] = useState<"local" | "external">("external");
  const [testOk, setTestOk] = useState(false);

  // Workspace & collection
  const [workspace, setWorkspace] = useState("");
  const [collection, setCollection] = useState("");
  const [collectionId, setCollectionId] = useState<string | null>(null);

  // Add documents
  const [docsLoaded, setDocsLoaded] = useState<"none" | "sample" | "upload">("none");
  const [uploadBusy, setUploadBusy] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function onKindChange(next: ProviderKind) {
    setKind(next);
    const defaults = KIND_DEFAULTS[next];
    setBaseUrl(defaults.base_url);
    setLocality(defaults.locality);
    setModel(defaults.model);
    setProviderName(defaults.label);
    setTestOk(false);
  }

  async function testAndCreateProvider() {
    setError(null);
    setBusy(true);
    try {
      const created = await apiJson<{ id: string }>("/admin/providers", {
        method: "POST",
        body: JSON.stringify({
          kind,
          name: providerName.trim(),
          base_url: baseUrl.trim(),
          models: [model.trim()],
          api_key: apiKey,
          locality,
        }),
      });
      const probe = await apiJson<{ ok: boolean; error?: string }>(
        `/admin/providers/${created.id}/test`,
        { method: "POST" },
      );
      if (!probe.ok) {
        setError(probe.error || "We couldn't connect with those details. Double-check the base URL and API key.");
        setTestOk(false);
        return;
      }
      setTestOk(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Provider setup failed");
      setTestOk(false);
    } finally {
      setBusy(false);
    }
  }

  async function createWorkspaceAndCollection() {
    setError(null);
    setBusy(true);
    try {
      const ws = await apiJson<{ id: string; name: string }>("/admin/workspaces", {
        method: "POST",
        body: JSON.stringify({ name: workspace.trim() }),
      });
      const col = await apiJson<{ id: string; name: string }>(
        `/admin/workspaces/${ws.id}/collections`,
        { method: "POST", body: JSON.stringify({ name: collection.trim() }) },
      );
      setCollectionId(col.id);
      setStep(3);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to create your workspace");
    } finally {
      setBusy(false);
    }
  }

  async function loadSampleDocuments() {
    if (!collectionId) return;
    setError(null);
    setUploadBusy(true);
    try {
      await apiJson(`/api/v1/collections/${collectionId}/sample-documents`, {
        method: "POST",
      });
      setDocsLoaded("sample");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Couldn't load the sample documents");
    } finally {
      setUploadBusy(false);
    }
  }

  async function onUploadOwnFiles(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!collectionId) return;
    const form = e.currentTarget;
    const fileInput = form.elements.namedItem("file") as HTMLInputElement;
    const files = fileInput.files;
    if (!files || files.length === 0) {
      setError("Choose at least one file to upload");
      return;
    }
    setError(null);
    setUploadBusy(true);
    try {
      for (const file of Array.from(files)) {
        const body = new FormData();
        body.append("file", file);
        const res = await apiFetch(`/api/v1/collections/${collectionId}/documents`, {
          method: "POST",
          body,
        });
        if (!res.ok) throw new ApiError(res.status, await res.text());
      }
      setDocsLoaded("upload");
      form.reset();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Upload failed");
    } finally {
      setUploadBusy(false);
    }
  }

  const suggestedQuestion =
    docsLoaded === "sample" ? SAMPLE_SUGGESTED_QUESTION : GENERIC_SUGGESTED_QUESTION;

  function goToChat() {
    navigate(`/chat?q=${encodeURIComponent(suggestedQuestion)}`);
  }

  return (
    <main
      className="mx-auto flex min-h-screen max-w-lg flex-col justify-center gap-6 px-6 py-10"
      data-testid="onboarding-wizard"
      aria-label="Guided setup"
    >
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Step {step + 1} of {STEPS.length}: {STEPS[step]}
        </p>
        <div className="mt-2 flex gap-1" aria-hidden="true">
          {STEPS.map((label, i) => (
            <div
              key={label}
              className={`h-1.5 flex-1 rounded-full ${i <= step ? "bg-primary" : "bg-muted"}`}
            />
          ))}
        </div>
      </div>

      {error ? (
        <p role="alert" className="text-sm text-destructive" data-testid="onboarding-error">
          {error}
        </p>
      ) : null}

      {step === 0 ? (
        <div className="space-y-4">
          <h1 className="text-3xl font-semibold tracking-tight">Welcome to SeismoBrain</h1>
          <p className="text-sm text-muted-foreground">
            You're signed in as <strong>{user?.email ?? "an admin"}</strong>. In the next few
            steps you'll connect an AI provider, create a workspace to hold your documents,
            add something to search, and try your first question. It takes about two minutes.
          </p>
          <Button onClick={() => setStep(1)}>Get started</Button>
        </div>
      ) : null}

      {step === 1 ? (
        <div className="space-y-3">
          <div>
            <h2 className="text-xl font-semibold">Connect an AI provider</h2>
            <p className="text-sm text-muted-foreground">
              SeismoBrain uses this to write answers from the passages it finds. It never
              sees your documents unless a question needs them.
            </p>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="prov">AI provider</Label>
            <Select value={kind} onValueChange={(v) => onKindChange(v as ProviderKind)}>
              <SelectTrigger id="prov" aria-label="LLM provider">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(Object.keys(KIND_DEFAULTS) as ProviderKind[]).map((k) => (
                  <SelectItem key={k} value={k}>
                    {KIND_DEFAULTS[k].label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="prov-name">Display name</Label>
            <Input id="prov-name" value={providerName} onChange={(e) => setProviderName(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="base-url">Base URL</Label>
            <Input
              id="base-url"
              value={baseUrl}
              onChange={(e) => {
                setBaseUrl(e.target.value);
                setTestOk(false);
              }}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="api-key">API key</Label>
            <Input
              id="api-key"
              type="password"
              autoComplete="off"
              value={apiKey}
              onChange={(e) => {
                setApiKey(e.target.value);
                setTestOk(false);
              }}
              placeholder={locality === "local" ? "Not required for a local server" : "sk-…"}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="model">Model id</Label>
            <Input id="model" value={model} onChange={(e) => setModel(e.target.value)} />
          </div>
          {testOk ? (
            <p className="text-sm text-success" data-testid="provider-test-ok">
              Connection test passed
            </p>
          ) : null}
          {testOk ? (
            <Button onClick={() => setStep(2)}>Next</Button>
          ) : (
            <Button
              disabled={(!apiKey.trim() && locality !== "local") || !baseUrl.trim() || !model.trim() || busy}
              onClick={() => void testAndCreateProvider()}
            >
              {busy ? "Testing…" : "Test connection & continue"}
            </Button>
          )}
        </div>
      ) : null}

      {step === 2 ? (
        <div className="space-y-3">
          <div>
            <h2 className="text-xl font-semibold">Name your workspace and collection</h2>
            <p className="text-sm text-muted-foreground">
              A workspace holds everything for one team or project. A collection is a folder
              of documents inside it. You can add more later.
            </p>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ws">Workspace name</Label>
            <Input
              id="ws"
              value={workspace}
              onChange={(e) => setWorkspace(e.target.value)}
              placeholder="e.g. Operations"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="col">First collection</Label>
            <Input
              id="col"
              value={collection}
              onChange={(e) => setCollection(e.target.value)}
              placeholder="e.g. Maintenance manuals"
            />
          </div>
          <Button
            disabled={!workspace.trim() || !collection.trim() || busy}
            onClick={() => void createWorkspaceAndCollection()}
          >
            {busy ? "Saving…" : "Next"}
          </Button>
        </div>
      ) : null}

      {step === 3 ? (
        <div className="space-y-4">
          <div>
            <h2 className="text-xl font-semibold">Add something to search</h2>
            <p className="text-sm text-muted-foreground">
              Load a few sample documents to try SeismoBrain right away, or upload your own.
            </p>
          </div>
          <div className="space-y-2 rounded-md border border-border p-4">
            <p className="text-sm font-medium">Option A: Try it with sample documents</p>
            <p className="text-sm text-muted-foreground">
              Three short files about a pump and its safety procedures.
            </p>
            <Button
              type="button"
              variant="outline"
              disabled={uploadBusy || docsLoaded === "sample"}
              onClick={() => void loadSampleDocuments()}
            >
              {docsLoaded === "sample" ? "Sample documents added" : "Load sample documents"}
            </Button>
          </div>
          <div className="space-y-2 rounded-md border border-border p-4">
            <p className="text-sm font-medium">Option B: Upload your own</p>
            <form className="flex flex-wrap items-center gap-3" onSubmit={onUploadOwnFiles}>
              <input
                id="file"
                name="file"
                type="file"
                multiple
                accept=".pdf,.md,.txt,.docx"
                className="text-sm"
              />
              <Button type="submit" variant="outline" size="sm" disabled={uploadBusy}>
                {uploadBusy ? "Uploading…" : "Upload"}
              </Button>
            </form>
            {docsLoaded === "upload" ? (
              <p className="text-sm text-success">Your files are on their way in.</p>
            ) : null}
          </div>
          <div className="flex gap-2">
            <Button disabled={docsLoaded === "none"} onClick={() => setStep(4)}>
              Next
            </Button>
            <Button variant="ghost" onClick={() => setStep(4)}>
              I'll add documents later
            </Button>
          </div>
        </div>
      ) : null}

      {step === 4 ? (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">You're set up</h2>
          <p className="text-sm text-muted-foreground">
            {docsLoaded === "none"
              ? "Your workspace is ready. Add documents any time from Documents, then come back to ask a question."
              : "Your documents are processing. This usually takes a few seconds for small files. Try asking:"}
          </p>
          {docsLoaded !== "none" ? (
            <p className="rounded-md border border-border bg-muted/50 p-3 text-sm font-medium">
              "{suggestedQuestion}"
            </p>
          ) : null}
          <Button onClick={goToChat} data-testid="onboarding-finish">
            Go to chat
          </Button>
        </div>
      ) : null}
    </main>
  );
}
