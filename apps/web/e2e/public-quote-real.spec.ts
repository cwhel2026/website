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
  const essential = page.getByRole("button", { name: "Essential only" });
  if (await essential.isVisible().catch(() => false)) {
    await essential.click();
  }

  await page.getByLabel("Postcode").fill(draft.postcode);
  await page.getByLabel("Town (optional)").fill(draft.town);
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
  await expect(page.getByText("Your estimated price")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText(/£[0-9]/).first()).toBeVisible();
  await expect(page.getByText(/inc\. VAT|Ex VAT|Travel|live pricing|not saved yet/i)).toHaveCount(0);
  await expect(page.getByText("Visit 1 — Cleaning and preparation")).toBeVisible();
  await expect(page.getByText("Visit 2 — Restoration coating")).toBeVisible();
  await expect(page.getByRole("button", { name: "Book me in ASAP" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Request a callback" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Email me my estimate" })).toBeVisible();

  await page.getByRole("button", { name: "Book me in ASAP" }).click();
  await page.getByLabel("Your name").fill("Test Customer");
  await page.getByLabel("Email").fill("mobile.book@example.co.uk");
  await page.getByLabel("Telephone").fill("07123456789");
  await page.getByLabel("Property address").fill("1 Test Lane");
  await page.getByRole("button", { name: "Book me in ASAP" }).click();

  const confirmation = page.getByRole("heading", { name: "What happens next" });
  const problem = page.locator("p.text-red-700");
  await expect(confirmation.or(problem)).toBeVisible({ timeout: 30_000 });
  if (await problem.isVisible()) {
    throw new Error(await problem.innerText());
  }
  await expect(page.getByText(/not a confirmed booking/i)).toBeVisible();
  await expect(page.getByText(/We have emailed/i)).toHaveCount(0);
  await expect(page.getByText(/Your appointment is not confirmed yet/i)).toBeVisible();

  const stored = await page.evaluate(() => sessionStorage.getItem("rmd_quote_draft"));
  expect(stored).toBeNull();
});