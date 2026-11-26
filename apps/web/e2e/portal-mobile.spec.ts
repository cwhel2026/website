import { test, expect, devices, type Page } from "@playwright/test";
import path from "node:path";

test.use({ ...devices["Desktop Chrome"] });

const MOBILE_WIDTHS = [375, 390, 430] as const;

const ROUTES = [
  "/dashboard",
  "/dashboard/calendar",
  "/dashboard/marketing/overview",
  "/dashboard/finance-hub",
  "/dashboard/quotations",
  "/dashboard/customers",
] as const;

const OUT = path.join("test-results", "portal-screenshots");

/** Layout-only: stubs a signed-in session and empty API responses (no backend needed). */
async function signedInWithEmptyApi(page: Page) {
  await page.addInitScript(() => localStorage.setItem("rmd_auth_token", "layout-test"));
  await page.route("**/api/v1/**", (route) =>
    route.request().url().includes("/auth/me")
      ? route.fulfill({ json: { email: "layout@test.local", role: "admin" } })
      : route.fulfill({ json: [] }),
  );
}

async function assertNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow, "page should not overflow horizontally").toBeLessThanOrEqual(2);
}

test("login page has no overflow", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/dashboard/login", { waitUntil: "networkidle" });
  await assertNoHorizontalOverflow(page);
});

for (const width of MOBILE_WIDTHS) {
  test.describe(`portal ${width}px`, () => {
    test.use({ viewport: { width, height: 844 } });

    for (const route of ROUTES) {
      test(route, async ({ page }) => {
        await signedInWithEmptyApi(page);
        await page.goto(route, { waitUntil: "networkidle" });
        await expect(page.getByRole("navigation", { name: "Primary" })).toBeVisible();
        await expect(page.getByRole("dialog", { name: "Cookie consent" })).toHaveCount(0);
        await assertNoHorizontalOverflow(page);
        await page.screenshot({
          path: path.join(OUT, `${width}${route.replace(/\//g, "_")}.png`),
        });
      });
    }
  });
}

test("desktop sidebar", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await signedInWithEmptyApi(page);
  await page.goto("/dashboard/finance-hub", { waitUntil: "networkidle" });
  await assertNoHorizontalOverflow(page);
  await page.screenshot({ path: path.join(OUT, "desktop_finance-hub.png") });
});
