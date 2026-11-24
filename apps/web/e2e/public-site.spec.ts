import { test, expect } from "@playwright/test";

test("homepage hero and quote CTA", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /don't replace your driveway/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /get my instant quote/i }).first()).toBeVisible();
});

test("quote wizard starts at location step", async ({ page }) => {
  await page.goto("/quote");
  await expect(page.getByRole("heading", { name: /provisional price/i })).toBeVisible();
  await expect(page.getByText("Location")).toBeVisible();
});

test("commercial enquiry form", async ({ page }) => {
  await page.goto("/commercial");
  await expect(page.getByRole("heading", { name: /partner with revive my drive/i })).toBeVisible();
});