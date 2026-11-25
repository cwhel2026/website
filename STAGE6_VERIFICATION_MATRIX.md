# Stage 6 / 6.1 / 6.2 — final verification matrix

**Prod verified** = owner evidence on Railway only (we do not mark it here).

| Requirement | Implemented | Automated tests | Prod verified | Notes |
|-------------|-------------|-----------------|---------------|-------|
| UK Ltd onboarding | Full | Yes | — | |
| FreeAgent OAuth + sync | Full | Partial | — | |
| Bills/expenses/reports cache | Full | Partial | — | |
| Distributable reserves (P&L+BS−tax−motion between fields; dividends) | Full | Partial | — | Blocked when mismatch |
| Receipt Telegram ingest | Full | Yes | — | Website → API |
| Receipt OCR | Partial | — | Blocked | Needs `OPENAI_API_KEY` |
| FA explanation attach | Full | Partial | — | `FINANCE_RECEIPT_FREEAGENT_ATTACH` |
| FA personal expense POST | Full | — | — | `FINANCE_RECEIPT_FREEAGENT_EXPENSE` + approval |
| Supplier bills via API | Unsupported | — | — | Manual in FA |
| Bookkeeping queue + approvals | Full | Yes | — | |
| Tax engine v2 | Full | Yes | Accountant | |
| Remuneration optimiser + blockers | Full | Yes | Accountant | |
| Cashflow 7/30/90/365 scenarios | Full | Partial | — | Provisional models |
| Daily/weekly/monthly/annual reports + Telegram | Full | Partial | — | Celery scheduled |
| Finance task centre | Full | Partial | — | Mon Telegram |
| Payroll FA read + guidance | Partial | — | — | No RTI submit |
| Accountant role + CSV (incl. bank) | Full | Partial | — | |
| Security audit endpoint | Full | Partial | — | Config evidence |
| Auto payments / HMRC file | Unsupported | — | — | Never |

**Merge path:** PRs #20 → #28 (6.2 stacks on #27). Migration **0010** after **0009**.

**Tests (local):** `pytest` in `apps/api`; Playwright `apps/web/e2e/finance-hub.spec.ts`.