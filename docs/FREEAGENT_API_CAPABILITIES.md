# FreeAgent API — verified in this codebase (Stage 6.1)

Official reference: https://dev.freeagent.com/docs  
Architecture rule: **FreeAgent is authoritative**; local rows are cache/review layers only.

## Verified read operations (implemented in `freeagent_client.py`)

| Operation | Method | Notes |
|-----------|--------|-------|
| OAuth + token refresh | `POST /v2/token_endpoint` | Existing |
| Company | `GET /v2/company` | Organisation name |
| Invoices | `GET /v2/invoices` | Matched to local invoices |
| Bank accounts | `GET /v2/bank_accounts` | |
| Bank transactions | `GET …/bank_transactions` | Paginated; stored locally by FA id |
| Bills | `GET /v2/bills` | Paginated cache |
| Expenses | `GET /v2/expenses` | Paginated cache |
| Categories | `GET /v2/categories` | For explanation categories |
| P&amp;L summary | `GET /v2/accounting/profit_and_loss/summary` | `from_date` / `to_date` (≤12 months) |
| Balance sheet summary | `GET /v2/accounting/balance_sheet/summary` | `as_at_date` optional |
| Trial balance summary | `GET /v2/accounting/trial_balance/summary` | |
| Payroll year | `GET /v2/payroll/{year}` | **Read-only**; requires permission level ≥7 |
| Payroll period | `GET /v2/payroll/{year}/{period}` | Period index from 0 |
| Payslips | `GET` via period resource | When payroll enabled |

## Verified write operations (guarded — approval required)

| Operation | Method | Notes |
|-----------|--------|-------|
| Bank transaction explanation + attachment | `PUT /v2/bank_transaction_explanations/{id}` | Base64 attachment ≤5MB in JSON body |
| Expense + attachment | `POST /v2/expenses` | Director personal reimbursement; `FINANCE_RECEIPT_FREEAGENT_EXPENSE` + approval |
| Bill + attachment | `POST` or `PUT /v2/bills` | No separate upload endpoint |

Writes are only called from **approved** receipt reconciliation flows; failures are logged, never fabricated as success.

## Not available / not implemented

| Capability | Status |
|------------|--------|
| HMRC RTI payroll **submission** via API | **Unsupported** — use FreeAgent UI; we track read-only status |
| Automatic bank payments | **Never implemented** |
| Distributable profits as dedicated API field | **Derived** from P&amp;L `retained-profit-carried-forward` when present in response |
| Historical P&amp;L beyond date rules | Limited by FA date-range rules (documented on each call) |
| Mettle direct API | **N/A** — bank feed via FreeAgent only |

## Payroll (FreeAgent built-in)

FreeAgent payroll is the preferred provider. This platform:

- Reads payroll periods, payment due dates, and filed status.
- Surfaces director salary **recommendations** from our tax engine (provisional).
- Does **not** submit RTI or calculate filed payslips without FreeAgent as source of truth.

Enable payroll in FreeAgent and connect OAuth with a user at permission level **7+**.

## Testing against sandbox

Set `FREEAGENT_API_BASE` to sandbox if applicable. All sync marks `last_sync_at`; watchdog flags stale data.