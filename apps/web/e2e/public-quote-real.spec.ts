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

  await expect(page.getByText("Minor wear around edges is perfectly normal.")).toBeVisible();
  await page.getByRole("button", { name: "I just want an estimate" }).click();

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

  const confirmation = page.getByRole("heading", { name: "Thank you for choosing SurfaceCoat" });
  const problem = page.locator("p.text-red-700");
  await expect(confirmation.or(problem)).toBeVisible({ timeout: 30_000 });
  if (await problem.isVisible()) {
    throw new Error(await problem.innerText());
  }
  await expect(page.getByText(/We've received your booking request/i)).toBeVisible();
  await expect(page.getByText(/This is a booking request/i)).toBeVisible();
  await expect(page.getByText(/We have emailed/i)).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Return to homepage" })).toBeVisible();

  const stored = await page.evaluate(() => sessionStorage.getItem("rmd_quote_draft"));
  expect(stored).toBeNull();
  await expect(page.getByRole("link", { name: "Add photographs later" })).toBeVisible();
});

test("upload a driveway photograph then still receive an estimate", async ({ page }) => {
  await page.goto("/quote");
  const essential = page.getByRole("button", { name: "Essential only" });
  if (await essential.isVisible().catch(() => false)) {
    await essential.click();
  }

  await page.getByLabel("Postcode").fill("L39 2YG");
  await page.getByLabel("Town (optional)").fill("Ormskirk");
  await page.getByRole("button", { name: "Check coverage" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByPlaceholder("Length (m)").first().fill("10");
  await page.getByPlaceholder("Width (m)").first().fill("4");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();

  await page.getByRole("button", { name: "Upload driveway photos" }).click();
  await page.getByTestId("gallery-input").setInputFiles("e2e/fixtures/driveway.jpg");
  await expect(page.getByRole("img", { name: "Driveway photograph" })).toBeVisible();
  await expect(page.getByText("Saved")).toBeVisible();
  await page.getByLabel("Notes (optional)").fill("Crack near the gate");
  await page.getByRole("button", { name: "See my estimate" }).click();

  await expect(page.getByText("Your estimated price")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText(/£[0-9]/).first()).toBeVisible();
  await expect(page.getByText(/inc\. VAT|Ex VAT|Travel|live pricing/i)).toHaveCount(0);

  await page.getByRole("button", { name: "Email me my estimate" }).click();
  await page.getByLabel("Your name").fill("Photo Customer");
  await page.getByLabel("Email").fill("mobile.photo@example.co.uk");
  await page.getByLabel("Property address").fill("2 Test Lane");
  await page.getByRole("button", { name: "Email my estimate" }).click();

  const confirmation = page.getByRole("heading", { name: "Thank you for choosing SurfaceCoat" });
  const problem = page.locator("p.text-red-700");
  await expect(confirmation.or(problem)).toBeVisible({ timeout: 30_000 });
  if (await problem.isVisible()) {
    throw new Error(await problem.innerText());
  }
  await expect(page.getByText(/This is a booking request/i)).toBeVisible();
});

test("the estimate appears on a slow connection while a photograph is still uploading", async ({ page }) => {
  const client = await page.context().newCDPSession(page);
  await client.send("Network.emulateNetworkConditions", {
    offline: false,
    latency: 400,
    downloadThroughput: (400 * 1024) / 8,
    uploadThroughput: (150 * 1024) / 8,
  });
  await page.route("**/api/v1/quotation-photos", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 12_000));
    try {
      await route.continue();
    } catch {
      /* The estimate is already on screen; the held upload can end with the page. */
    }
  });

  await page.goto("/quote");
  const essential = page.getByRole("button", { name: "Essential only" });
  if (await essential.isVisible().catch(() => false)) {
    await essential.click();
  }
  await page.getByLabel("Postcode").fill("L39 2YG");
  await page.getByLabel("Town (optional)").fill("Ormskirk");
  await page.getByRole("button", { name: "Check coverage" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByPlaceholder("Length (m)").first().fill("10");
  await page.getByPlaceholder("Width (m)").first().fill("4");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();

  await page.getByRole("button", { name: "Upload driveway photos" }).click();
  await page.getByTestId("gallery-input").setInputFiles("e2e/fixtures/driveway.jpg");
  await expect(page.getByRole("progressbar")).toBeVisible();
  const started = Date.now();
  await page.getByRole("button", { name: "See my estimate" }).click();
  await expect(page.getByText("Your estimated price")).toBeVisible({ timeout: 8_000 });
  expect(Date.now() - started).toBeLessThan(8_000);
  await expect(page.getByText(/Uploading|Preparing/)).toBeVisible();
  await expect(page.getByText(/does not wait for them/i)).toBeVisible();
});

test("a failed photograph upload can be retried without losing the quotation", async ({ page }) => {
  let attempts = 0;
  await page.route("**/api/v1/quotation-photos", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    attempts += 1;
    if (attempts < 4) {
      await route.fulfill({ status: 500, contentType: "application/json", body: "{\"detail\":\"again\"}" });
      return;
    }
    await route.continue();
  });

  await page.goto("/quote");
  const essential = page.getByRole("button", { name: "Essential only" });
  if (await essential.isVisible().catch(() => false)) {
    await essential.click();
  }
  await page.getByLabel("Postcode").fill("L39 2YG");
  await page.getByLabel("Town (optional)").fill("Ormskirk");
  await page.getByRole("button", { name: "Check coverage" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByPlaceholder("Length (m)").first().fill("8");
  await page.getByPlaceholder("Width (m)").first().fill("3");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Upload driveway photos" }).click();
  await page.getByLabel("Notes (optional)").fill("Close-up of a crack");
  await page.getByTestId("gallery-input").setInputFiles("e2e/fixtures/driveway.jpg");
  await expect(page.getByRole("button", { name: "Retry upload" })).toBeVisible({ timeout: 8_000 });
  await expect(page.getByLabel("Notes (optional)")).toHaveValue("Close-up of a crack");
  await expect(page.getByRole("img", { name: "Driveway photograph" })).toBeVisible();
  await page.getByRole("button", { name: "Retry upload" }).click();
  await expect(page.getByText("Saved")).toBeVisible();
  await page.getByRole("button", { name: "I just want an estimate" }).click();
  await expect(page.getByText("Your estimated price")).toBeVisible({ timeout: 30_000 });
});

test("a callback request keeps the estimate and does not confirm a visit", async ({ page }) => {
  await page.goto("/quote");
  const essential = page.getByRole("button", { name: "Essential only" });
  if (await essential.isVisible().catch(() => false)) {
    await essential.click();
  }
  await page.getByLabel("Postcode").fill("L39 2YG");
  await page.getByLabel("Town (optional)").fill("Ormskirk");
  await page.getByRole("button", { name: "Check coverage" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByPlaceholder("Length (m)").first().fill("8");
  await page.getByPlaceholder("Width (m)").first().fill("3");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "I just want an estimate" }).click();
  await expect(page.getByText("Your estimated price")).toBeVisible({ timeout: 30_000 });
  await page.getByRole("button", { name: "Request a callback" }).click();
  await page.getByLabel("Your name").fill("Callback Customer");
  await page.getByLabel("Email").fill("mobile.callback@example.co.uk");
  await page.getByLabel("Telephone").fill("07123456780");
  await page.getByLabel("Best time to call").fill("Weekday mornings");
  await page.getByLabel("Property address").fill("2 Test Lane");
  await page.getByRole("button", { name: "Request my callback" }).click();
  await expect(page.getByRole("heading", { name: "Thank you for choosing SurfaceCoat" })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText(/callback request/i)).toBeVisible();
  await expect(page.getByText(/This is a booking request/i)).toBeVisible();
});