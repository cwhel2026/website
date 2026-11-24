import { test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const OUT = process.env.MEDIA_AUDIT_OUT ?? "/opt/cursor/artifacts/media-audit";

const PUBLIC_PATHS = [
  "/",
  "/services",
  "/services/tarmac-restoration",
  "/services/block-paving",
  "/services/imprinted-concrete",
  "/services/minor-repairs",
  "/services/commercial-car-parks",
  "/commercial",
  "/quote",
  "/service-areas",
  "/areas/tarmac-restoration-blackpool",
  "/gallery",
  "/faq",
  "/contact",
];

test.describe("public media audit screenshots", () => {
  for (const route of PUBLIC_PATHS) {
    test(`${route} desktop`, async ({ page }, testInfo) => {
      fs.mkdirSync(OUT, { recursive: true });
      await page.goto(route, { waitUntil: "networkidle" });
      await page.waitForTimeout(400);
      const slug = route === "/" ? "home" : route.replace(/\//g, "_").replace(/^_/, "");
      const file = path.join(OUT, `${slug}-desktop.png`);
      await page.screenshot({ path: file, fullPage: true });
      await testInfo.attach("screenshot", { path: file, contentType: "image/png" });
    });
  }

  test("/ homepage mobile", async ({ page }, testInfo) => {
    fs.mkdirSync(OUT, { recursive: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/", { waitUntil: "networkidle" });
    await page.waitForTimeout(400);
    const file = path.join(OUT, "home-mobile.png");
    await page.screenshot({ path: file, fullPage: true });
    await testInfo.attach("screenshot", { path: file, contentType: "image/png" });
  });

  test("/services mobile", async ({ page }, testInfo) => {
    fs.mkdirSync(OUT, { recursive: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/services", { waitUntil: "networkidle" });
    const file = path.join(OUT, "services-mobile.png");
    await page.screenshot({ path: file, fullPage: true });
    await testInfo.attach("screenshot", { path: file, contentType: "image/png" });
  });
});