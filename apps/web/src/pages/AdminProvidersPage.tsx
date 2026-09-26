/**
 * @file AdminProvidersPage.tsx
 * @description List, edit, and remove configured LLM providers (admin)
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-17
 * @version 0.4.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { ApiError } from "@/api/client";
import {
  createProvider,
  deleteProvider,
  listProviders,
  testProvider,
  updateProvider,
  type ProviderKind,
  type ProviderLocality,
  type ProviderRow,
} from "@/api/services/providers";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/components/ui/sonner";

const KIND_OPTIONS: { value: ProviderKind; label: string }[] = [
  { value: "openai_compatible", label: "OpenAI-compatible / OpenRouter" },
  { value: "ollama_vllm", label: "Ollama / vLLM" },
  { value: "anthropic", label: "Anthropic" },
  { value: "gemini", label: "Gemini" },
];

const KIND_DEFAULTS: Record<ProviderKind, { name: string; baseUrl: string; model: string; locality: ProviderLocality }> = {
  openai_compatible: { name: "OpenAI-compatible / OpenRouter", baseUrl: "https://openrouter.ai/api/v1", model: "openai/gpt-4o-mini", locality: "external" },
  ollama_vllm: { name: "Ollama / vLLM", baseUrl: "http://127.0.0.1:11434/v1", model: "llama3.2", locality: "local" },
  anthropic: { name: "Anthropic", baseUrl: "https://api.anthropic.com", model: "claude-3-5-haiku-latest", locality: "external" },
  gemini: { name: "Gemini", baseUrl: "https://generativelanguage.googleapis.com", model: "gemini-2.0-flash", locality: "external" },
};

function asKind(value: string): ProviderKind {
  if (
    value === "openai_compatible" ||
    value === "ollama_vllm" ||
    value === "anthropic" ||
    value === "gemini"
  ) {
    return value;
  }
  return "openai_compatible";
}

function asLocality(value: string): ProviderLocality {
  return value === "local" ? "local" : "external";
}

export function AdminProvidersPage() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const q = useQuery({
    queryKey: ["admin-providers"],
    queryFn: listProviders,
  });

  const [editing, setEditing] = useState<ProviderRow | null>(null);
  const [adding, setAdding] = useState(false);
  const [removing, setRemoving] = useState<ProviderRow | null>(null);

  const [name, setName] = useState("");
  const [kind, setKind] = useState<ProviderKind>("openai_compatible");
  const [baseUrl, setBaseUrl] = useState("");
  const [model, setModel] = useState("");
  const [locality, setLocality] = useState<ProviderLocality>("external");
  const [apiKey, setApiKey] = useState("");

  useEffect(() => {
    if (!editing) return;
    setName(editing.name);
    setKind(asKind(editing.kind));
    setBaseUrl(editing.base_url);
    setModel(editing.models[0] ?? "");
    setLocality(asLocality(editing.locality));
    setApiKey("");
  }, [editing]);

  function onError(err: unknown, fallback: string) {
    toast.error(err instanceof ApiError ? err.detail : fallback);
  }

  function resetToDefaults(nextKind: ProviderKind = "openai_compatible") {
    const defaults = KIND_DEFAULTS[nextKind];
    setKind(nextKind);
    setName(defaults.name);
    setBaseUrl(defaults.baseUrl);
    setModel(defaults.model);
    setLocality(defaults.locality);
    setApiKey("");
  }

  function openAddProvider() {
    resetToDefaults();
    setAdding(true);
  }

  function onAddKindChange(value: string) {
    resetToDefaults(asKind(value));
  }

  const add = useMutation({
    mutationFn: async () => {
      const created = await createProvider({
        kind,
        name: name.trim(),
        base_url: baseUrl.trim(),
        models: [model.trim()],
        locality,
        ...(apiKey.trim() ? { api_key: apiKey.trim() } : {}),
      });
      const probe = await testProvider(created.id);
      return { probe };
    },
    onSuccess: ({ probe }) => {
      void qc.invalidateQueries({ queryKey: ["admin-providers"] });
      void qc.invalidateQueries({ queryKey: ["providers"] });
      setAdding(false);
      if (probe.ok) {
        toast.success("Provider added and connection OK");
      } else {
        toast.success("Provider added");
        toast.error(probe.error || "Connection test failed. Check the details.");
      }
    },
    onError: (err) => onError(err, "Couldn't add that provider"),
  });

  const save = useMutation({
    mutationFn: async () => {
      if (!editing) throw new Error("No provider selected");
      const payload = {
        kind,
        name: name.trim(),
        base_url: baseUrl.trim(),
        models: [model.trim()],
        locality,
        ...(apiKey.trim() ? { api_key: apiKey.trim() } : {}),
      };
      const updated = await updateProvider(editing.id, payload);
      const probe = await testProvider(editing.id);
      return { updated, probe };
    },
    onSuccess: ({ probe }) => {
      void qc.invalidateQueries({ queryKey: ["admin-providers"] });
      void qc.invalidateQueries({ queryKey: ["providers"] });
      setEditing(null);
      if (probe.ok) {
        toast.success("Provider updated and connection OK");
      } else {
        toast.success("Provider updated");
        toast.error(probe.error || "Connection test failed. Check the details.");
      }
    },
    onError: (err) => onError(err, "Couldn't update that provider"),
  });

  const remove = useMutation({
    mutationFn: (id: string) => deleteProvider(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["admin-providers"] });
      void qc.invalidateQueries({ queryKey: ["providers"] });
      setRemoving(null);
      toast.success("Provider removed");
    },
    onError: (err) => onError(err, "Couldn't remove that provider"),
  });

  function onSave(e: FormEvent) {
    e.preventDefault();
    save.mutate();
  }

  function onAdd(e: FormEvent) {
    e.preventDefault();
    add.mutate();
  }

  return (
    <main className="mx-auto max-w-3xl space-y-4 px-6 py-10" data-testid="admin-providers">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-3xl font-semibold">Providers</h1>
        {(q.data?.providers.length ?? 0) > 0 ? (
          <Button type="button" onClick={openAddProvider}>Add provider</Button>
        ) : null}
      </div>
      {q.isError ? (
        <p role="alert" className="text-sm text-destructive">
          Failed to load providers
        </p>
      ) : null}
      {q.isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : (
      <ul className="divide-y rounded border">
        {(q.data?.providers ?? []).map((p) => (
          <li
            key={p.id}
            className="flex flex-col gap-3 px-3 py-3 sm:flex-row sm:items-center sm:justify-between"
            data-testid={`provider-row-${p.id}`}
          >
            <div className="min-w-0 text-sm">
              <div className="font-medium">{p.name}</div>
              <div className="text-foreground/70">
                {p.kind} · {p.locality} · {p.base_url}
              </div>
              <div className="text-foreground/60">{p.models.join(", ")}</div>
            </div>
            <div className="flex shrink-0 gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                data-testid={`provider-edit-${p.id}`}
                onClick={() => setEditing(p)}
              >
                Edit
              </Button>
              <Button
                type="button"
                variant="destructive"
                size="sm"
                data-testid={`provider-remove-${p.id}`}
                onClick={() => setRemoving(p)}
              >
                Remove
              </Button>
            </div>
          </li>
        ))}
      </ul>
      )}
      {(q.data?.providers.length ?? 0) === 0 && !q.isLoading ? (
        <EmptyState
          title="No providers configured. Add one here or use Guided Setup for the complete first-time setup."
          action={(
            <div className="flex flex-wrap justify-center gap-2">
              <Button type="button" onClick={openAddProvider}>Add provider</Button>
              <Button type="button" variant="outline" onClick={() => navigate("/onboarding")}>Use Guided Setup</Button>
            </div>
          )}
        />
      ) : null}

      <Dialog open={adding} onOpenChange={setAdding}>
        <DialogContent data-testid="provider-add-dialog">
          <DialogHeader>
            <DialogTitle>Add provider</DialogTitle>
            <DialogDescription>
              Enter the connection details. SeismoBrain will save the provider and test the connection.
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-3" onSubmit={onAdd}>
            <div className="space-y-1.5">
              <Label htmlFor="add-prov-kind">Kind</Label>
              <Select value={kind} onValueChange={onAddKindChange}>
                <SelectTrigger id="add-prov-kind" aria-label="Provider kind"><SelectValue /></SelectTrigger>
                <SelectContent>{KIND_OPTIONS.map((opt) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="add-prov-name" required>Name</Label>
              <Input id="add-prov-name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="add-prov-url" required>Base URL</Label>
              <Input id="add-prov-url" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="add-prov-model" required>Model</Label>
              <Input id="add-prov-model" value={model} onChange={(e) => setModel(e.target.value)} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="add-prov-key">API key</Label>
              <Input id="add-prov-key" type="password" autoComplete="off" placeholder={locality === "local" ? "Not required for a local server" : "Enter API key"} value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setAdding(false)}>Cancel</Button>
              <Button type="submit" disabled={add.isPending || !name.trim() || !baseUrl.trim() || !model.trim() || (locality !== "local" && !apiKey.trim())}>
                {add.isPending ? "Adding…" : "Add and test"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={editing != null} onOpenChange={(open) => !open && setEditing(null)}>
        <DialogContent data-testid="provider-edit-dialog">
          <DialogHeader>
            <DialogTitle>Edit provider</DialogTitle>
            <DialogDescription>
              Update connection details. Leave the API key blank to keep the current secret.
            </DialogDescription>
          </DialogHeader>
          <form className="space-y-3" onSubmit={onSave}>
            <div className="space-y-1.5">
              <Label htmlFor="edit-prov-name" required>
                Name
              </Label>
              <Input
                id="edit-prov-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-prov-kind">Kind</Label>
              <Select value={kind} onValueChange={(v) => setKind(asKind(v))}>
                <SelectTrigger id="edit-prov-kind" aria-label="Provider kind">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {KIND_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-prov-url" required>
                Base URL
              </Label>
              <Input
                id="edit-prov-url"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-prov-model" required>
                Model
              </Label>
              <Input
                id="edit-prov-model"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-prov-locality">Locality</Label>
              <Select
                value={locality}
                onValueChange={(v) => setLocality(asLocality(v))}
              >
                <SelectTrigger id="edit-prov-locality" aria-label="Provider locality">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="local">Local</SelectItem>
                  <SelectItem value="external">External</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-prov-key">API key</Label>
              <Input
                id="edit-prov-key"
                type="password"
                autoComplete="off"
                placeholder="Leave blank to keep current"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditing(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={save.isPending || !name.trim() || !baseUrl.trim() || !model.trim()}>
                {save.isPending ? "Saving…" : "Save"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={removing != null} onOpenChange={(open) => !open && setRemoving(null)}>
        <DialogContent data-testid="provider-remove-dialog">
          <DialogHeader>
            <DialogTitle>Remove provider?</DialogTitle>
            <DialogDescription>
              {removing
                ? `This removes “${removing.name}” from SeismoBrain. Chat will use any remaining providers.`
                : null}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setRemoving(null)}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={remove.isPending || !removing}
              data-testid="provider-remove-confirm"
              onClick={() => removing && remove.mutate(removing.id)}
            >
              {remove.isPending ? "Removing…" : "Remove"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </main>
  );
}
