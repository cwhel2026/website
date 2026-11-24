# Public website redesign (acquisition engine)

## Shipped in this pass

- **Design system:** asphalt / stone / restore-green palette, Fraunces + DM Sans, premium button styles (distinct from dashboard emerald cards).
- **Homepage:** hero with headline, before/after slider (illustrative), services grid, why restore, how it works, restore vs replace, live territory coverage check, commercial teaser, FAQ, final CTA.
- **Multi-step quote wizard:** 7 steps, session persistence, funnel events (consent-gated), live pricing via `POST /api/v1/quotations/instant`.
- **Public API:** `GET /api/v1/public/coverage`, `POST /api/v1/public/commercial-enquiry`.
- **Commercial** landing + CRM pipeline integration.
- **Service pages** rebuilt with shared premium template.
- **SEO:** `sitemap.xml`, `robots.txt`, Open Graph defaults.
- **Mobile:** sticky quote bar, touch-friendly wizard.
- **GDPR:** analytics consent banner (no pixels until granted).
- **Dashboard:** Website & marketing scaffold page.
- **Playwright** smoke tests (run against deployed URL with `PLAYWRIGHT_BASE_URL`).

## Honest gaps (next iterations)

- CMS / landing page builder / A/B engine (dashboard stub only).
- Real project photography (gallery empty by design).
- Photo upload on quote path, address autocomplete, Meta/GA4 tags (behind consent UI only).
- Service enable/disable from dashboard driving public catalogue (still API `is_active`).

## Verify

```bash
cd apps/web && npm run build
PLAYWRIGHT_BASE_URL=https://your-site.up.railway.app npx playwright test
```