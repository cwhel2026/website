import { test, expect } from "@playwright/test";

/** GET-only checks through the same proxy the browser uses. */

test("session identifies the test account", async ({ request }) => {
  const res = await request.get("/api/v1/auth/me");
  expect(res.status()).toBe(200);
  const me = await res.json();
  expect(me.email?.toLowerCase()).toBe(process.env.E2E_EMAIL?.toLowerCase());
  if (process.env.E2E_EXPECT_ROLE) expect(String(me.role).toUpperCase()).toBe(process.env.E2E_EXPECT_ROLE.toUpperCase());
});

test("database schema is at Alembic head", async ({ request }) => {
  const res = await request.get("/api/v1/ops/schema");
  expect(res.status()).toBe(200);
  const report = await res.json();
  test.info().annotations.push({ type: "schema", description: JSON.stringify(report) });
  expect(report.at_head, `alembic ${report.alembic_current} vs head ${report.alembic_head}`).toBe(true);
  expect(report.blocking_drift ?? [], "blocking drift").toEqual([]);
});

test("worker health endpoint reports status", async ({ request }) => {
  const res = await request.get("/api/v1/ops/workers");
  expect(res.status()).toBe(200);
  const report = await res.json();
  test.info().annotations.push({ type: "workers", description: JSON.stringify(report) });
  expect(typeof report.overall).toBe("string");
  if (process.env.E2E_EXPECT_WORKERS_OK === "1") expect(report.overall).toBe("ok");
});

test("marketing overview and growth fund load", async ({ request }) => {
  for (const path of ["/api/v1/marketing/surfacecoat/overview", "/api/v1/finance/growth-fund/ledger"]) {
    const res = await request.get(path);
    expect(res.status(), path).toBe(200);
  }
});

test("unauthenticated requests are rejected", async ({ playwright, baseURL }) => {
  const anon = await playwright.request.newContext({ baseURL, storageState: { cookies: [], origins: [] } });
  for (const path of ["/api/v1/auth/me", "/api/v1/ops/workers", "/api/v1/finance/invoices", "/api/v1/crm/enquiries"]) {
    expect((await anon.get(path)).status(), path).toBe(401);
  }
  await anon.dispose();
});
