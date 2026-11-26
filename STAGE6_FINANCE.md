# Stage 6 — UK Ltd financial platform

Architecture: **Mettle → FreeAgent → Revive AI Finance Director**. FreeAgent is authoritative; this platform adds onboarding, sync audit, planning tax constants, remuneration, receipts, and watchdog alerts.

## Verification matrix (all phases)

| Phase | PR | Migrations | Tested locally |
|-------|-----|------------|----------------|
| A Onboarding + FreeAgent | [#20](https://github.com/cwhel2026/website/pull/20) | 0004 | Yes |
| B Bookkeeping + receipts | [#21](https://github.com/cwhel2026/website/pull/21) | 0005 | Yes |
| C Tax + compliance | [#23](https://github.com/cwhel2026/website/pull/23) | 0006 | Yes |
| D Remuneration | [#24](https://github.com/cwhel2026/website/pull/24) | 0007 | Yes |
| E Watchdog + Telegram finance | [#25](https://github.com/cwhel2026/website/pull/25) | — | Yes |
| F Accountant + exports | [#26](https://github.com/cwhel2026/website/pull/26) | 0008 | Yes |
| 6.1 FreeAgent completion + reports | [#27](https://github.com/cwhel2026/website/pull/27) (stack) | 0009 | Yes |
| 6.2 Production readiness | [#29](https://github.com/cwhel2026/website/pull/29) (stack) | 0010 | Yes |

See `STAGE6_VERIFICATION_MATRIX.md`, `RAILWAY_FINANCE_ENV.md`, and `RAILWAY_STAGE6_FINANCE.md`.

**Production verified:** owner must merge stack, run migrations 0004–0008, set env vars, connect FreeAgent, and confirm Telegram/worker on API service.

## Phase summaries

**A:** Company setup wizard, encrypted FreeAgent tokens, bank sync audit, corporation tax stub.

**B:** Categorisation, review queue, Telegram receipt photos, Money hub, `generate_finance_token_encryption_key.py`.

**C:** Versioned tax rules, marginal relief, VAT monitor, tax reserves, compliance calendar, Tax centre UI.

**D:** Salary/dividend optimiser, dividend proposals (approval only), director's loan, Director pay UI.

**E:** Financial watchdog, cash flow forecast, territory profitability API, Telegram finance answers, daily alerts.

**F:** `accountant` role, CSV exports, accountant review/tax summary endpoints.

## Generate `FINANCE_TOKEN_ENCRYPTION_KEY`

```bash
python apps/api/scripts/generate_finance_token_encryption_key.py
```

Paste the single line into Railway on the **API** service. The vault derives a Fernet key via SHA-256 of this material (minimum 16 characters; script prints a URL-safe 48-byte token).

## Credentials / env

| Variable | Service | Purpose |
|----------|---------|---------|
| `FREEAGENT_*` | API | OAuth |
| `FINANCE_TOKEN_ENCRYPTION_KEY` | API | Token encryption |
| `FINANCE_RECEIPTS_DIR` | API | Persistent receipt storage |
| `FINANCE_TELEGRAM_INGEST_KEY` | API + website | Next.js receipt forward |
| `API_INTERNAL_URL` | website | Forward Telegram to FastAPI |
| `OPENAI_API_KEY` | API | Receipt OCR (optional) |

## FreeAgent API — verified in code

OAuth, company, invoices, bank accounts, bank transactions. Bills/expenses/attachments: not yet integrated — documented in code.

## Professional review required

Remuneration strategy, VAT scheme, corporation tax filings, dividend legality, any output with `requires_accountant_review` or `provisional: true`.

## Known limits

- Not HMRC filing software; no automatic bank payments.
- Dividends blocked when distributable profit &lt; cash.
- Web-only deploy: finance APIs and receipt OCR require API or combined image.
- FreeAgent remains authoritative — local expenses are planning/review layers unless accountant confirms.