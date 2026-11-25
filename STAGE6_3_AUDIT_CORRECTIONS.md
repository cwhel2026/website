# Stage 6.3 — independent audit correction report

**Date:** 2025-11-25 (Europe/London)  
**Scope:** Tax engine, remuneration, reserves, receipts, cashflow, reporting, migrations, security  
**Production verified:** No — configuration and automated test evidence only

## 1. UK tax engine

| Issue | Root cause | Fix | Tests |
|-------|------------|-----|-------|
| Single hardcoded rule pack | `ACTIVE_RULES` only | `rules_for_date()`, `RULES_2025_26`, `RULES_2026_27` with `verified_on` + source URLs | `test_tax_engine_reference.py` |
| PA taper missing | Not implemented | `tapered_personal_allowance()` | taper at £125,140 |
| NI UEL / 2% band | Flat rate only | Primary + UEL split in `employee_ni_on_salary` | reference NI test |
| CT associated cos / short periods | Missing | `_prorated_limits()` in marginal relief | boundary £50k CT |
| VAT forward test | Rolling only | Forward invoiced window in `vat_monitor.py` | monitor fields |

**Files:** `services/tax_engine/*.py`

## 2. Remuneration optimiser

| Issue | Root cause | Fix |
|-------|------------|-----|
| NI before IT | Wrong taxable base | Gross salary + `incremental_income_tax_on_salary` |
| £3k / 3 dividend points | Coarse search | £500 steps; all feasible dividends in range |
| Target-only ranking | Sort key | Sort by `combined_tax_gbp` then target gap |
| Cash obligations | Ignored | `obligation_reserve_gbp` on inputs |

**Files:** `services/remuneration/optimizer.py`, `routers/remuneration.py`

## 3. Distributable reserves

| Issue | Fix |
|-------|-----|
| `capital_and_reserves` misuse | Removed; only retained profit keys |
| Single source | Require P&L **and** BS retained match |
| Double CT deduction | Removed; retained treated post-tax |
| Stale sync | Block if FreeAgent sync >7 days |

**Files:** `services/finance/distributable_reserves.py`

## 4. Tax reserves

| Issue | Fix |
|-------|-----|
| All-time invoice/expense sum | FA P&L net profit for CT when synced |
| 17% VAT guess | Unknown unless VAT registered |
| Zero PAYE | `unknown` status when PAYE not confirmed |
| Sync = reliable | `data_stale` if >168h; `has_unknown_liabilities` |

**Files:** `services/finance/tax_reserves.py`

## 5. Receipt accounting

| Issue | Fix |
|-------|-----|
| Unmatched → personal | `UNMATCHED` unless payment method keywords |
| Backup Path("") | `_valid_backup_root()` strips empty |
| Atomic writes | `.part` + `os.replace` + SHA verify |
| Telegram “sent” on queue | `telegram_sent=False` until outbox delivery |

**Files:** `receipt_accounting.py`, `document_store.py`, `financial_reports.py`, `notifications/outbox.py`

## 6. Cash flow

| Issue | Fix |
|-------|-----|
| Historical expenses as future | Removed; statutory calendar + dated invoices |
| Double marketing | Removed duplicate expense pass |
| Invoice + job double count | Jobs skipped when invoice exists |
| 8% tax slice | Full obligation reserve from tax reserves |

**Files:** `services/finance/cashflow.py`

## 7. Annual reporting

| Issue | Fix |
|-------|-----|
| Monthly cron vs year-end day | Daily 07:15 check; `annual_report_idempotency_key` |
| March 1 fallback | Removed — requires company accounting reference |
| False telegram_sent | Delivered only after outbox success |

**Files:** `worker/celery_app.py`, `worker/tasks.py`, `financial_reports.py`

## 8. Railway / combined deploy

Documented in `RAILWAY_FINANCE_ENV.md` (unchanged): split vs combined, `API_INTERNAL_URL=http://127.0.0.1:8000`, receipt volume on API only.

## 9. Migration 0001

| Issue | Fix |
|-------|-----|
| Empty `upgrade()` | No-op when `users`/`territories`/`customers` exist; stamps baseline |

**File:** `alembic/versions/20251124_0001_initial_schema.py`

## 10. Security

Security audit now checks ephemeral `/tmp` storage, backup not CWD, mount writable.

## Remaining blockers

- Live FreeAgent read-only verification (owner credentials)
- Accountant sign-off on distributable reserves and remuneration
- PAYE amounts from FreeAgent payroll when enabled
- Opening bank cash requires reconciled FreeAgent bank balance (currently unknown if unsynced)

## Test evidence

Run: `cd apps/api && PYTHONPATH=. pytest -q`
Playwright: `apps/web/e2e/finance-hub.spec.ts`