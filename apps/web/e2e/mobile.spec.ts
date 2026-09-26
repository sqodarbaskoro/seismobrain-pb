/**
 * @file mobile.spec.ts
 * @description Mobile-viewport smoke checks — regression coverage for responsive layout changes.
 *   Full multi-step desktop workflows stay chromium-only; this file only exercises the pieces
 *   that actually change shape at a phone width (nav drawer, chat composer, table→card layout).
 * @author Sri Yanto Qodarbaskoro
 * @contact sqodarbaskoro@gmail.com
 * @linkedin https://www.linkedin.com/in/sqodarbaskoro/
 * @website https://www.seismopilot.com
 * @created 2026-09-17
 * @modified 2026-09-18
 * @version 0.1.2
 * @copyright © 2026 Sri Yanto Qodarbaskoro
 */

import { expect, test, type Page } from "@playwright/test";
import { loginAsAdmin } from "./auth";

/** No horizontal scroll at this viewport — catches the class of bug where a fixed-width layout
 *  piece (a grid column, a table) forces the page wider than the screen. */
async function expectNoHorizontalOverflow(page: Page) {
  const overflowing = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth + 1,
  );
  expect(overflowing).toBe(false);
}

test("chat composer is reachable and usable on a phone viewport", async ({ page, request }) => {
  await loginAsAdmin(page, request);
  await page.goto("/chat");
  await expect(page.getByTestId("chat-page")).toBeVisible();
  await expectNoHorizontalOverflow(page);

  // Conversation list is collapsed by default below md.
  await expect(page.getByTestId("conversation-list")).toBeHidden();
  await page.getByRole("button", { name: "Chats" }).click();
  await expect(page.getByTestId("conversation-list")).toBeVisible();
  await expect(page.getByTestId("new-chat-button")).toBeVisible();
  await page.getByTestId("new-chat-button").click();
  await expect(page.getByTestId("conversation-list")).toBeHidden();

  await page.getByLabel("Message").fill("What is torque?");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByTestId("message-list")).not.toContainText("Ask a question about");
  await expect(page.getByTestId("user-message")).toHaveText("What is torque?");
  await page.getByRole("button", { name: "Chats", exact: true }).click();
  const deleteChat = page.getByRole("button", { name: "Delete chat: What is torque?", exact: true }).first();
  await expect(deleteChat).toBeEnabled();
  await expectNoHorizontalOverflow(page);
  await deleteChat.click();
  await page.getByRole("dialog").getByRole("button", { name: "Delete", exact: true }).click();
  await expect(page.getByTestId("user-message")).toHaveCount(0);
});

test("admin tables collapse into cards on a phone viewport", async ({ page, request }) => {
  await loginAsAdmin(page, request);
  await page.goto("/people/users");
  await expect(page.getByTestId("admin-users")).toBeVisible();
  await expect(page.locator("table")).toBeHidden();
  await expectNoHorizontalOverflow(page);
});

test("documents page has no horizontal overflow on a phone viewport", async ({ page, request }) => {
  await loginAsAdmin(page, request);
  await page.goto("/library");
  await expect(page.getByTestId("documents-page")).toBeVisible();
  await expectNoHorizontalOverflow(page);
});
