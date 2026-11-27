import { defineConfig, devices } from "@playwright/test";

/**
 * Authenticated projects run only when E2E_EMAIL / E2E_PASSWORD are supplied through
 * protected environment variables (CI secrets). See docs/E2E_TESTING.md.
 */
const authenticated = Boolean(process.env.E2E_EMAIL && process.env.E2E_PASSWORD);
const AUTH_STATE = "test-results/.auth/session.json";

export default defineConfig({
  testDir: "e2e",
  timeout: 60_000,
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  projects: [
    { name: "mobile", testIgnore: /authenticated\/|public-quote-real/, use: { ...devices["iPhone 13"] } },
    { name: "desktop", testIgnore: /authenticated\/|public-quote-real/, use: { ...devices["Desktop Chrome"] } },
    {
      name: "public-quote-mobile",
      testMatch: /public-quote-real\.spec\.ts/,
      // iPhone 13 device profile + Chromium (CI installs chromium only; still mobile viewport/touch).
      use: { ...devices["iPhone 13"], browserName: "chromium" },
    },
    ...(authenticated
      ? [
          { name: "auth-setup", testMatch: /authenticated\/auth\.setup\.ts/ },
          {
            name: "authenticated-mobile",
            testMatch: /authenticated\/.*\.spec\.ts/,
            dependencies: ["auth-setup"],
            use: { ...devices["Pixel 7"], storageState: AUTH_STATE },
          },
          {
            name: "authenticated-desktop",
            testMatch: /authenticated\/.*\.spec\.ts/,
            dependencies: ["auth-setup"],
            use: { ...devices["Desktop Chrome"], storageState: AUTH_STATE },
          },
        ]
      : []),
  ],
});
