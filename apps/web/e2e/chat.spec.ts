/**
 * @file chat.spec.ts
 * @description Chat page shell e2e against authenticated session (no demo data)
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-16
 * @modified 2026-09-18
 * @version 0.5.0
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { expect, test } from "@playwright/test";
import { loginAsAdmin } from "./auth";

test.beforeEach(async ({ page, request }) => {
  await loginAsAdmin(page, request);
});

test("chat page", async ({ page }) => {
  await page.goto("/chat");
  await expect(page.getByTestId("chat-page")).toBeVisible();
  await expect(page.getByTestId("conversation-list")).toBeAttached();
  await expect(page.getByTestId("message-list")).toBeVisible();
  await expect(page.getByTestId("composer")).toBeVisible();
  await page.getByTestId("new-chat-button").click();
  await page.getByLabel("Message").fill("What is torque?");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByTestId("message-list")).not.toContainText("Ask a question about");
  await expect(page.getByTestId("user-message")).toHaveText("What is torque?");
});

test("new chats keep named conversations and restore history after switching and refresh", async ({ page }) => {
  await page.goto("/chat");
  await page.getByTestId("new-chat-button").click();
  const firstQuestion = `Explain torque ${Date.now()}`;
  await page.getByLabel("Message").fill(firstQuestion);
  await page.getByRole("button", { name: "Send", exact: true }).click();
  const firstChat = page.getByTestId("conversation-list").getByRole("button", { name: firstQuestion, exact: true });
  await expect(firstChat).toBeEnabled();
  // A grounded answer renders as "assistant-answer"; a typed refusal (e.g. no LLM
  // provider configured for this scenario) renders as its own "refusal-callout" —
  // either is a valid response to restore, so accept whichever one showed up.
  const firstResponse = page.getByTestId("assistant-answer").or(page.getByTestId("refusal-callout"));
  await expect(firstResponse).toBeVisible();
  const firstAnswer = await firstResponse.innerText();
  expect(firstAnswer.length).toBeGreaterThan(0);

  await page.getByTestId("new-chat-button").click();
  await expect(page.getByTestId("user-message")).toHaveCount(0);
  await page.getByLabel("Message").fill("Explain wave propagation");
  await page.getByRole("button", { name: "Send", exact: true }).click();
  const secondChat = page.getByTestId("conversation-list").getByRole("button", { name: "Explain wave propagation", exact: true });
  await expect(secondChat).toBeEnabled();

  await firstChat.click();
  await expect(page.getByTestId("user-message")).toHaveText(firstQuestion);
  await expect(firstResponse).toHaveText(firstAnswer, { useInnerText: true });
  await page.reload();
  await expect(page.getByTestId("user-message")).toHaveText(firstQuestion);
  await expect(firstResponse).toHaveText(firstAnswer, { useInnerText: true });
  await secondChat.click();
  await expect(page.getByTestId("user-message")).toHaveText("Explain wave propagation");
});

test("scope bar", async ({ page }) => {
  await page.goto("/chat");
  await expect(page.getByTestId("scope-bar")).toBeVisible();
});

test("short titles persist and chats can be cancelled or deleted", async ({ page }) => {
  await page.goto("/chat");
  await page.getByTestId("new-chat-button").click();
  const question = "What is the recommended procedure for preparing a field survey?";
  const title = "What is the recommended procedure for...";
  await page.getByLabel("Message").fill(question);
  await page.getByRole("button", { name: "Send", exact: true }).click();
  const firstChat = page.getByTestId("conversation-list").getByRole("button", { name: title, exact: true });
  await expect(firstChat).toBeEnabled();
  await page.reload();
  await expect(firstChat).toBeVisible();
  await expect(page.getByTestId("user-message")).toHaveText(question);

  await page.getByTestId("new-chat-button").click();
  await page.getByLabel("Message").fill("Explain acoustic sources");
  await page.getByRole("button", { name: "Send", exact: true }).click();
  const deleteFirst = page.getByRole("button", { name: `Delete chat: ${title}`, exact: true });
  await expect(deleteFirst).toBeEnabled();
  await deleteFirst.click();
  await page.getByRole("dialog").getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(firstChat).toBeVisible();
  await expect(page.getByTestId("user-message")).toHaveText("Explain acoustic sources");

  await deleteFirst.click();
  await page.getByRole("dialog").getByRole("button", { name: "Delete", exact: true }).click();
  await expect(firstChat).toHaveCount(0);
  await expect(page.getByTestId("user-message")).toHaveText("Explain acoustic sources");
  await page.getByRole("button", { name: "Delete chat: Explain acoustic sources", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Delete", exact: true }).click();
  await expect(page.getByTestId("user-message")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Copy", exact: true })).toHaveCount(0);
  await expect(page).not.toHaveURL(/conversation=/);
  await page.reload();
  await expect(firstChat).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Delete chat: Explain acoustic sources", exact: true })).toHaveCount(0);
});

test("a failed deletion keeps the chat available", async ({ page }) => {
  await page.goto("/chat");
  await page.getByTestId("new-chat-button").click();
  await page.getByLabel("Message").fill("Chat to keep after failed deletion");
  await page.getByRole("button", { name: "Send", exact: true }).click();
  const deleteChat = page.getByRole("button", { name: "Delete chat: Chat to keep after failed deletion", exact: true });
  await expect(deleteChat).toBeEnabled();
  await page.route("**/api/v1/conversations/*", async (route) => {
    if (route.request().method() === "DELETE") {
      await route.fulfill({ status: 500, json: { detail: "Could not delete conversation" } });
    } else {
      await route.continue();
    }
  });
  await deleteChat.click();
  await page.getByRole("dialog").getByRole("button", { name: "Delete", exact: true }).click();
  await expect(page.getByRole("dialog").getByRole("alert")).toHaveText("Could not delete conversation");
  await page.getByRole("dialog").getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(deleteChat).toBeEnabled();
  await expect(page.getByTestId("user-message")).toHaveText("Chat to keep after failed deletion");
});

test("a11y", async ({ page }) => {
  await page.goto("/chat");
  await expect(page.getByLabel("Conversation list")).toBeVisible();
  await expect(page.getByLabel("Active thread")).toBeVisible();
  await page.getByRole("button", { name: "Toggle theme" }).click();
  await expect(page.getByTestId("chat-page")).toHaveClass(/dark/);
});

test("path template", async ({ page }) => {
  await page.goto("/path-template");
  await expect(page.getByTestId("path-template-tester")).toBeVisible();
  await page.getByRole("button", { name: "Test template" }).click();
  await expect(page.getByTestId("path-template-result")).toContainText("matched");
});

test("why this answer", async ({ page }) => {
  await page.goto("/chat");
  await page.getByTestId("why-answer-toggle").click();
  await expect(page.getByTestId("why-this-answer")).toBeVisible();
  await expect(page.getByTestId("why-query-variants")).toBeVisible();
  await expect(page.getByTestId("why-filters")).toBeVisible();
  await expect(page.getByTestId("why-ranked-evidence")).toBeVisible();
  await expect(page.getByTestId("why-grounding-summary")).toContainText("Grounding");

  // Once a real message streams back, the panel shows the actual retrieval trace
  // (the resolved query, route, source count, latency), not a placeholder string.
  await page.getByTestId("new-chat-button").click();
  await page.getByLabel("Message").fill("What is torque?");
  await page.getByRole("button", { name: "Send", exact: true }).click();
  await expect(page.getByTestId("message-list")).not.toContainText("Ask a question about");
  await expect(page.getByTestId("why-query-variants")).toContainText("What is torque?");
  await expect(page.getByTestId("why-retrieval-stats")).toContainText("route=");
});

test("provider badge", async ({ page }) => {
  await page.goto("/chat");
  await expect(page.getByTestId("provider-badge")).toBeVisible();
});

test("mvp smoke", async ({ page }) => {
  await page.goto("/chat");
  await expect(page.getByTestId("chat-page")).toBeVisible();
  await expect(page.getByTestId("scope-bar")).toBeVisible();
  await expect(page.getByTestId("composer")).toBeVisible();
});
