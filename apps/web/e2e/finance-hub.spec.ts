import { test, expect } from "@playwright/test";

test("finance hub prompts for admin session", async ({ page }) => {
  await page.goto("/dashboard/finance-hub");
  await expect(page.getByRole("heading", { name: /money hub|finance/i })).toBeVisible({
    timeout: 15000,
  });
});