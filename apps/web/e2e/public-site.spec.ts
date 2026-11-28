import { test, expect } from "@playwright/test";

test("homepage hero and quote CTA", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Don’t replace it. Restore it." })).toBeVisible();
  await expect(page.getByRole("link", { name: "Get my instant estimate" }).first()).toBeVisible();
  const box = await page.getByRole("link", { name: "Get my instant estimate" }).first().boundingBox();
  const viewport = page.viewportSize();
  expect(box).not.toBeNull();
  expect(viewport).not.toBeNull();
  expect(box!.y + box!.height).toBeLessThan(viewport!.height);
});

test("public navigation reaches each section", async ({ page }) => {
  await page.goto("/");
  const essential = page.getByRole("button", { name: "Essential only" });
  if (await essential.isVisible().catch(() => false)) await essential.click();
  for (const label of ["Our services", "Transformations", "How it works", "Areas we cover", "Contact"]) {
    const menu = page.getByRole("button", { name: "Menu" });
    const mobile = await menu.isVisible();
    if (mobile) await menu.click();
    const nav = mobile
      ? page.getByRole("navigation", { name: "Mobile" })
      : page.getByRole("navigation", { name: "Primary" });
    await nav.getByRole("link", { name: label }).click();
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await page.goto("/");
  }
});

test("quote wizard starts at location step", async ({ page }) => {
  await page.goto("/quote");
  await expect(page.getByRole("heading", { name: "Your instant estimate" })).toBeVisible();
  await expect(page.getByText("Location").first()).toBeVisible();
});

test("commercial enquiry form", async ({ page }) => {
  await page.goto("/commercial");
  await expect(page.getByRole("heading", { name: "Commercial surface restoration" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Submit commercial enquiry" })).toBeVisible();
});


test("public launch pages have no obsolete March launch notice", async ({ page }) => {
  for (const path of ["/", "/quote", "/contact", "/commercial"]) {
    const response = await page.goto(path);
    expect(response?.status()).toBe(200);
    await expect(page.getByText(/March 2027/i)).toHaveCount(0);
  }
});
