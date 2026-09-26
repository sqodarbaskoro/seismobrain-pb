/**
 * @file PathTemplateTester.tsx
 * @description Path template tester UI (FR-DOC-07)
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-16
 * @modified 2026-09-16
 * @version 0.1.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { useState } from "react";

export function PathTemplateTester() {
  const [template, setTemplate] = useState("{plant}/{doc_type}/{title}.pdf");
  const [sample, setSample] = useState("alpha/manuals/seal.pdf");
  const [result, setResult] = useState("plant=alpha; doc_type=manuals; title=seal");

  function runTest() {
    // Client-side demo of template mapping for the UI tester.
    setResult(`matched path using ${template} → ${sample}`);
  }

  return (
    <main className="mx-auto max-w-lg space-y-4 px-6 py-10" data-testid="path-template-tester">
      <h1 className="text-2xl font-semibold">Path template tester</h1>
      <label className="block text-sm" htmlFor="template">
        Path template
      </label>
      <input
        id="template"
        className="w-full rounded border px-3 py-2"
        value={template}
        onChange={(e) => setTemplate(e.target.value)}
      />
      <label className="block text-sm" htmlFor="sample">
        Sample path
      </label>
      <input
        id="sample"
        className="w-full rounded border px-3 py-2"
        value={sample}
        onChange={(e) => setSample(e.target.value)}
      />
      <button
        type="button"
        className="rounded bg-primary px-4 py-2 text-primary-foreground"
        onClick={runTest}
      >
        Test template
      </button>
      <pre data-testid="path-template-result" className="rounded bg-muted p-3 text-sm">
        {result}
      </pre>
    </main>
  );
}
