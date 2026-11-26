import type { Page } from "@playwright/test";

/** The only mutating requests the authenticated suite may send. */
const ALLOWED_MUTATIONS = ["/api/v1/auth/login", "/api/v1/auth/logout"];

/**
 * Aborts every non-GET request leaving the browser (except sign-in/out), so the suite
 * cannot create records, send messages or trigger ad spend even against production.
 * Returns the list of blocked requests so tests can assert pages do not mutate on load.
 */
export async function enforceReadOnly(page: Page): Promise<string[]> {
  const blocked: string[] = [];
  await page.route("**/*", (route) => {
    const req = route.request();
    const method = req.method();
    if (method === "GET" || method === "HEAD" || method === "OPTIONS") return route.continue();
    const { pathname } = new URL(req.url());
    if (ALLOWED_MUTATIONS.includes(pathname)) return route.continue();
    blocked.push(`${method} ${pathname}`);
    return route.abort("blockedbyclient");
  });
  return blocked;
}
