# SurfaceCoat Growth Fund

## How it works

- **5%** of **eligible customer revenue** (ex-VAT when matched to an invoice) credits the **virtual marketing reserve** ledger.
- **FreeAgent / Mettle** bank lines (`SyncSource.FREEAGENT`) are the source; Mettle has **no automated pot API** — use **virtual reserve** + optional manual Mettle pot moves.
- **Excluded:** internal transfers, director capital, loans, VAT-only lines, duplicates, unreconciled lines (unless matched to invoice).
- **Refunds** create negative ledger adjustments.
- **£150/week** advertising cap is **unchanged** until owner increases approved limits; available fund does **not** auto-authorise spend.

## API

- `GET /api/v1/finance/growth-fund/summary`
- `GET /api/v1/finance/growth-fund/ledger`
- `PATCH /api/v1/finance/growth-fund/settings` — `allocation_pct`, `enabled`
- `POST /api/v1/finance/growth-fund/record-initial-launch` — record £600 when genuinely funded
- `POST /api/v1/finance/growth-fund/process-allocations`

Runs automatically after **FreeAgent bank sync** (daily worker).

## UI

- Marketing → **Growth fund**
- Money hub → Growth Fund card

## Migration

`20251126_0016_growth_fund.py` (requires `0015` on same branch).