import { test, expect, devices } from "@playwright/test";
import path from "node:path";

test.use({ ...devices["Desktop Chrome"] });

const MOBILE_WIDTHS = [375, 390, 430] as const;

const ROUTES = [
  "/dashboard/login",
  "/dashboard",
  "/dashboard/calendar",
  "/dashboard/marketing/overview",
  "/dashboard/finance-hub",
] as const;

async function assertNoHorizontalOverflow(page: import("@playwright/test").Page) {
  const overflow = await page.evaluate(() => {
    const doc = document.documentElement;
    return doc.scrollWidth > doc.clientWidth + 2;
  });
  expect(overflow, "page should not overflow horizontally").toBeFalsy();
}

for (const width of MOBILE_WIDTHS) {
  test.describe(`portal mobile ${width}px`, () => {
    test.use({ viewport: { width, height: 812 } });

    for (const route of ROUTES) {
      test(`screenshot and overflow ${route}`, async ({ page }) => {
        await page.goto(route, { waitUntil: "networkidle" });
        await assertNoHorizontalOverflow(page);
        const safe = route.replace(/\//g, "_").replace(/^_/, "");
        await page.screenshot({
          path: path.join("e2e", "screenshots", `portal-${width}-${safe}.png`),
          fullPage: true,
        });
      });
    }
  });
}

test.describe("portal desktop", () => {
  test("home layout", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/dashboard/login", { waitUntil: "networkidle" });
    await assertNoHorizontalOverflow(page);
    await page.screenshot({
      path: path.join("e2e", "screenshots", "portal-desktop-login.png"),
      fullPage: true,
    });
  });
});