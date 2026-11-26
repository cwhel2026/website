# Authenticated browser tests

Two layers:

| Suite | Backend | Runs where |
|-------|---------|-----------|
| `e2e/portal-mobile.spec.ts` | Stubbed (layout only) | Locally, any time |
| `e2e/authenticated/*` | **Real** API + Postgres | CI job `web-e2e-authenticated`, and on demand against production |

The authenticated suite signs in through the real login page, then visits the key portal pages at
mobile (Pixel 7) and desktop sizes. Each page must:

- load with no API 5xx (503 "not configured" is allowed and must render as such);
- show no `NaN`, `undefined` or sample-data buttons;
- not overflow horizontally on mobile;
- send **no** mutating request while loading.

Full-page screenshots go to `apps/web/test-results/authenticated-screenshots/`.

## Non-destructive by construction

`e2e/authenticated/guard.ts` aborts every browser request that is not GET/HEAD/OPTIONS, except
`/api/v1/auth/login` and `/api/v1/auth/logout`. The API checks in `api.spec.ts` are GET only. The
suite therefore cannot create records, send customer messages, launch campaigns or post financial
entries, even if a page tried to.

The suite should run as the **auditor** account, which the API itself restricts to read-only:
every POST/PUT/PATCH/DELETE from an auditor returns 403, regardless of the browser guard.

## Provisioning the production test account

The account is created by the API at startup from two environment variables. No password is ever
typed into chat or committed.

1. Generate a password locally (at least 16 characters):

   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(24))"
   ```

2. Railway → **website** service → **Variables**:

   ```text
   E2E_AUDITOR_EMAIL=portal-auditor@<your-domain>
   E2E_AUDITOR_PASSWORD=<generated value>
   ```

   Redeploy. On start the API creates (or updates) a user with role **AUDITOR**. It refuses to
   proceed if the email belongs to the owner or to any existing non-auditor account, and refuses
   passwords shorter than 16 characters.

3. GitHub → repository → **Settings → Secrets and variables → Actions → New repository secret**:

   | Secret | Value |
   |--------|-------|
   | `PROD_E2E_EMAIL` | the same email |
   | `PROD_E2E_PASSWORD` | the same password |
   | `PROD_BASE_URL` | `https://<your production domain>` |

4. Run **Actions → Production read-only checks → Run workflow**. Screenshots and the HTML report are
   attached to the run.

**Revoke:** delete `E2E_AUDITOR_PASSWORD` from Railway but **keep** `E2E_AUDITOR_EMAIL`, then
redeploy. On start the account is deactivated (existing sessions stop working because inactive users
are rejected). Delete the GitHub secrets too. **Rotate:** change both values and redeploy.

## Running locally

```bash
# terminal 1 – API (migrates, seeds the auditor from env)
cd apps/api
export DATABASE_URL=postgresql+asyncpg://… SYNC_DATABASE_URL=postgresql://… JWT_SECRET=… \
       E2E_AUDITOR_EMAIL=e2e-auditor@example.com E2E_AUDITOR_PASSWORD=<16+ chars>
python -m app.schema.cli upgrade && uvicorn app.main:app --port 8000

# terminal 2 – web, production build, same-origin proxy like Railway
cd apps/web
npm run build && API_INTERNAL_URL=http://127.0.0.1:8000 npx next start -p 3000

# terminal 3
cd apps/web
E2E_EMAIL=e2e-auditor@example.com E2E_PASSWORD=<same> E2E_EXPECT_ROLE=AUDITOR \
  npx playwright test --project=authenticated-mobile --project=authenticated-desktop
```

Optional: `E2E_EXPECT_WORKERS_OK=1` makes the worker-health check require overall status `ok`.
