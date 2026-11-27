import { test, expect, type Page } from "@playwright/test";
import path from "node:path";
import { enforceReadOnly } from "./guard";

const ROUTES = [
  "/dashboard",
  "/dashboard/launch-readiness",
  "/dashboard/system-health",
  "/dashboard/tax-centre",
  "/dashboard/director-pay",
  "/dashboard/finance-hub",
  "/dashboard/expenses",
  "/dashboard/invoices",
  "/dashboard/marketing/overview",
  "/dashboard/marketing/campaigns",
  "/dashboard/marketing/growth-fund",
  "/dashboard/advertising",
  "/dashboard/commercial-leads",
  "/dashboard/calendar",
  "/dashboard/customers",
  "/dashboard/quotations",
  "/dashboard/approvals",
  "/dashboard/analytics",
] as const;

const OUT = path.join("test-results", "authenticated-screenshots");

/** 503 is the API's "not configured / disconnected" signal, which pages must render as such. */
function isServerFault(status: number) {
  return status >= 500 && status !== 503;
}

async function assertNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow, "page should not overflow horizontally").toBeLessThanOrEqual(2);
}

for (const route of ROUTES) {
  test(`${route} renders real data without faults`, async ({ page }, testInfo) => {
    const blocked = await enforceReadOnly(page);
    const faults: string[] = [];
    page.on("response", (res) => {
      const url = new URL(res.url());
      if (url.pathname.startsWith("/api/v1/") && isServerFault(res.status())) {
        faults.push(`${res.status()} ${url.pathname}`);
      }
    });

    await page.goto(route, { waitUntil: "networkidle" });
    await expect(page).toHaveURL(new RegExp(`${route}/?$`), { timeout: 15_000 });

    const body = page.locator("main");
    await expect(body).toBeVisible();
    const text = await body.innerText();
    expect(text, "no NaN values").not.toMatch(/\bNaN\b/);
    expect(text, "no undefined values").not.toMatch(/£undefined|\bundefined\b/);
    expect(text, "no sample-data buttons").not.toMatch(/add sample|load sample|sample data/i);

    if ((page.viewportSize()?.width ?? 1280) < 768) {
      await expect(page.getByRole("navigation", { name: "Primary" })).toBeVisible();
    }
    await assertNoHorizontalOverflow(page);

    await page.screenshot({
      path: path.join(OUT, `${testInfo.project.name}${route.replace(/\//g, "_")}.png`),
      fullPage: true,
    });

    expect(faults, "API server errors while loading page").toEqual([]);
    expect(blocked, "page attempted to mutate data on load").toEqual([]);
  });
}

test("system health shows worker and schema status", async ({ page }) => {
  await enforceReadOnly(page);
  await page.goto("/dashboard/system-health", { waitUntil: "networkidle" });
  await expect(page.getByTestId("worker-overall")).toBeVisible();
  await expect(page.getByTestId("schema-status")).toBeVisible();
});

test("command centre links to launch readiness", async ({ page }) => {
  await enforceReadOnly(page);
  await page.goto("/dashboard", { waitUntil: "networkidle" });
  await page.getByRole("link", { name: /launch centre/i }).first().click();
  await expect(page.getByRole("heading", { name: "Launch centre", exact: true })).toBeVisible();
  await assertNoHorizontalOverflow(page);
});
