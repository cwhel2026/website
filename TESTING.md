# Testing

## Automated (Phase 1)

- **API unit tests**: pricing engine, postcode parsing — no database required.
- **CI**: GitHub Actions `api-tests` + `web-build`.

## Planned (spec section 31)

Integration tests with PostgreSQL for booking conflicts, concurrent quotes, territory profitability, etc.

## Running locally

```bash
cd apps/api && pytest -q
cd apps/web && npm run build
```

Use synthetic data only; never commit real customer or financial records.