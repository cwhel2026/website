import { test as setup, expect } from "@playwright/test";
import { enforceReadOnly } from "./guard";

const AUTH_STATE = "test-results/.auth/session.json";

setup("sign in through the real login page", async ({ page }) => {
  const email = process.env.E2E_EMAIL;
  const password = process.env.E2E_PASSWORD;
  if (!email || !password) throw new Error("E2E_EMAIL and E2E_PASSWORD must be set (use CI secrets, never commit them)");

  await enforceReadOnly(page);
  await page.goto("/dashboard/login");
  await page.locator('input[name="email"]').fill(email);
  await page.locator('input[name="password"]').fill(password);
  await page.getByRole("button", { name: /sign in|log in/i }).click();
  await page.waitForURL(/\/dashboard\/?$/, { timeout: 30_000 });

  const cookies = await page.context().cookies();
  const session = cookies.find((c) => c.name === "sc_session");
  expect(session, "session cookie set").toBeTruthy();
  expect(session!.httpOnly, "session cookie must be HttpOnly").toBe(true);
  expect(cookies.find((c) => c.name === "sc_csrf"), "CSRF cookie set").toBeTruthy();
  expect(await page.evaluate(() => localStorage.getItem("rmd_auth_token")), "no token in localStorage").toBeNull();
  expect(await page.evaluate(() => document.cookie.includes("sc_session")), "session not readable by JS").toBe(false);

  await page.context().storageState({ path: AUTH_STATE });
});
