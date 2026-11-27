import { test, expect } from "@playwright/test";

/**
 * Public instant quote — real API (no auth). Runs in CI against migrated Postgres + API.
 * Pricing must not be mocked; travel distance is computed server-side.
 */

test("complete provisional tarmac quote on mobile", async ({ page }) => {
  const draft = {
    postcode: "L39 2YG",
    town: "Ormskirk",
    service_slug: "tarmac-driveway-restoration",
    surface_type: "tarmac",
    surface_condition: "fair",
    sections: [{ label: "Main driveway", length_m: "10", width_m: "4", area_sqm: "" }],
    requires_washing: true,
    customer_washed_already: false,
  };
  await page.goto("/quote");

  await page.getByLabel("Postcode").fill(draft.postcode);
  await page.getByRole("button", { name: "Check coverage" }).click();
  await page.getByRole("button", { name: "Continue" }).click();

  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByPlaceholder("Length (m)").first().fill(draft.sections[0].length_m);
  await page.getByPlaceholder("Width (m)").first().fill(draft.sections[0].width_m);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();

  await page.getByRole("button", { name: "Calculate estimate" }).click();

  await expect(page.getByText(/Internal Server Error/i)).toHaveCount(0);
  await expect(page.getByText(/provisional/i).first()).toBeVisible({ timeout: 30_000 });
  const price = page.locator("text=/£[0-9]/");
  await expect(price.first()).toBeVisible({ timeout: 30_000 });

  const stored = await page.evaluate(() => sessionStorage.getItem("rmd_quote_draft"));
  expect(stored).toContain(draft.postcode);
});