import "./chat-thinking.css";

const STAGE_LABEL: Record<string, string> = {
  routing: "Routing…",
  retrieving: "Retrieving evidence…",
  generating: "Generating…",
  verifying: "Verifying citations…",
};

export function ChatThinking({
  streaming = false,
  stage,
}: {
  streaming?: boolean;
  /** Server-emitted SSE stage ("routing" | "retrieving" | "generating" | "verifying"),
   * shown in place of the generic label when known. */
  stage?: string | null;
}) {
  const label = (stage && STAGE_LABEL[stage]) || (streaming ? "Responding…" : "Thinking…");
  return (
    <div className="chat-thinking" role="status" aria-live="polite" aria-atomic="true">
      <span className="chat-thinking__dots" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
      <span>{label}</span>
    </div>
  );
}
