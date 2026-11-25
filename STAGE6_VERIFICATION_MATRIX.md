# Stage 6 requirement verification matrix

Legend: **Full** · **Partial** · **Tests** · **Prod** · **Blocked** · **Unsupported** · **Accountant**

| Requirement | Status | Tests | Prod | Notes |
|-------------|--------|-------|------|-------|
| UK Ltd onboarding wizard | Full | Yes | Blocked | Needs merge + migration 0004 |
| FreeAgent OAuth + encrypted tokens | Full | Yes | Blocked | Credentials on API |
| Bank + invoice sync | Full | Yes | Blocked | |
| Bills + expenses cache | Full | Partial | Blocked | GET /v2/bills, /expenses |
| P&L / balance sheet / trial balance | Full | Partial | Blocked | Accounting summary endpoints |
| Distributable profit from FA | Partial | Partial | Blocked | From P&L retained profit field when present |
| Receipt Telegram ingest | Full | Yes | Blocked | API or API_INTERNAL_URL forward |
| Receipt OCR | Partial | — | Blocked | Needs OPENAI_API_KEY |
| FreeAgent receipt attach | Partial | — | Blocked | PUT explanation; needs explanation URL + approval |
| Bookkeeping categorisation + queue | Full | Yes | Blocked | |
| Tax engine (versioned rules) | Full | Yes | Accountant | Provisional planning only |
| VAT monitor + tax reserves | Full | Yes | Blocked | |
| Compliance calendar | Full | Partial | Blocked | Dates from company profile |
| Salary/dividend optimiser | Partial | Yes | Accountant | Uses FA distributable when cached |
| Dividend proposals (no payment) | Full | Partial | Accountant | |
| Director's loan | Partial | Yes | Blocked | From flagged personal txns |
| FreeAgent payroll read | Partial | — | Blocked | No RTI submit — **Unsupported** |
| Financial watchdog + Telegram | Full | Partial | Blocked | |
| Daily / weekly finance reports | Partial | — | Blocked | Monthly/annual via API generate |
| Cash flow forecast | Partial | Yes | Blocked | Conservative invoice/expense model |
| Job/territory profitability | Partial | Yes | Blocked | Existing engine |
| Accountant role + CSV export | Full | Partial | Blocked | Migration 0008 |
| Automated bank payments | Unsupported | — | — | Never implemented |
| HMRC filing via platform | Unsupported | — | — | FreeAgent / accountant |

**Production verified** = empty until owner completes `RAILWAY_STAGE6_FINANCE.md` checklist on live Railway.

**Next hardening:** FreeAgent expense creation from receipts (POST /v2/expenses), payslip PDF fetch when payroll enabled, monthly report Celery schedule, expanded Playwright finance smoke tests.