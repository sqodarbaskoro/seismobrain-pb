/**
 * @file ChatAnswer.test.tsx
 * @description Chat answer renders flowing prose without raw [E#] markers
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-19
 * @version 0.2.1
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ChatAnswer } from "./ChatAnswer";

const sentences = [
  {
    text: "The Device Controller determines the exact trigger time [E5].",
    evidence: ["E5"],
    support: "supported",
  },
  {
    text: "It determines which module to start [E6].",
    evidence: ["E6"],
    support: "partial",
  },
];

describe("ChatAnswer", () => {
  it("renders flowing prose without raw evidence markers", () => {
    render(
      <ChatAnswer
        sentences={sentences}
        citations={{
          E5: { evidence_id: "E5", title: "Device Controller" },
          E6: { evidence_id: "E6", title: "Source selection" },
        }}
        evidenceText={{}}
        onCite={vi.fn()}
      />,
    );

    const answer = screen.getByTestId("assistant-answer");
    expect(answer).toHaveTextContent("The Device Controller determines the exact trigger time.");
    expect(answer).toHaveTextContent("It determines which module to start.");
    expect(answer.textContent).not.toMatch(/\[E\d+\]/);
    expect(screen.getByRole("heading", { name: "Sources" })).toBeInTheDocument();
    expect(screen.getByText("Device Controller")).toBeInTheDocument();
  });

  it("keeps citation chips and support badges, hiding supported labels", () => {
    const onCite = vi.fn();
    render(
      <ChatAnswer
        sentences={sentences}
        citations={{
          E5: { evidence_id: "E5", title: "Device Controller" },
          E6: { evidence_id: "E6", title: "Source selection" },
        }}
        evidenceText={{}}
        onCite={onCite}
      />,
    );

    const chips = screen.getAllByTestId("citation-chip");
    expect(chips.length).toBeGreaterThan(0);
    fireEvent.click(chips[0]);
    expect(onCite).toHaveBeenCalledWith("E5");

    const badges = screen.getAllByTestId("support-badge");
    expect(badges).toHaveLength(2);
    expect(badges[0]).toHaveClass("sr-only");
    expect(badges[1]).toHaveClass("sr-only");
    expect(badges[1]).toHaveTextContent("partial");
    expect(screen.getByTestId("grounding-note")).toHaveTextContent(
      "One claim is only partly supported by the sources.",
    );
  });

  it("numbers the same document as one source and lists distinct pages", () => {
    const onCite = vi.fn();
    render(
      <ChatAnswer
        sentences={[
          {
            text: "The Device Controller determines the exact trigger time [E5].",
            evidence: ["E5", "E6"],
            support: "supported",
          },
          {
            text: "It assigns a batch number [E7].",
            evidence: ["E7"],
            support: "supported",
          },
          {
            text: "It is used in field operations [E10].",
            evidence: ["E10"],
            support: "supported",
          },
        ]}
        citations={{
          E5: { evidence_id: "E5", title: "Device Controller", page: 3 },
          E6: { evidence_id: "E6", title: "Device Controller", page: 3 },
          E7: { evidence_id: "E7", title: "Device Controller", page: 5 },
          E10: { evidence_id: "E10", title: "Device Controller", page: 12 },
        }}
        evidenceText={{}}
        onCite={onCite}
      />,
    );

    const chips = screen.getAllByTestId("citation-chip");
    expect(chips).toHaveLength(3);
    expect(chips.map((chip) => chip.textContent)).toEqual(["1", "1", "1"]);
    expect(screen.getAllByTestId("answer-source")).toHaveLength(1);
    expect(screen.getByText("Device Controller")).toBeInTheDocument();
    expect(screen.queryByText(/Device Controller ·/)).not.toBeInTheDocument();
    const pages = screen.getAllByTestId("source-page");
    expect(pages.map((page) => page.textContent)).toEqual(["p.3", "p.5", "p.12"]);
    fireEvent.click(pages[1]);
    expect(onCite).toHaveBeenCalledWith("E7");
  });

  it("collapses same-document citations to one source when pages are unknown", () => {
    render(
      <ChatAnswer
        sentences={[
          { text: "One [E5].", evidence: ["E5"], support: "supported" },
          { text: "Two [E6].", evidence: ["E6"], support: "supported" },
        ]}
        citations={{
          E5: { evidence_id: "E5", title: "Device Controller" },
          E6: { evidence_id: "E6", title: "Device Controller" },
        }}
        evidenceText={{}}
        onCite={vi.fn()}
      />,
    );

    expect(screen.getAllByTestId("citation-chip").map((chip) => chip.textContent)).toEqual([
      "1",
      "1",
    ]);
    expect(screen.getAllByTestId("answer-source")).toHaveLength(1);
    expect(screen.queryByTestId("source-pages")).not.toBeInTheDocument();
  });
});
