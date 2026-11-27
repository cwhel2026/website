# Phase 4 finance review

Changes: aggregate proposed campaign budget checks, fail closed on reserve errors, reconciled invoice-linked growth allocations, bounded invoice-linked refund reversals, partial bank import reporting, connection row locking, isolated growth processing, linked FreeAgent invoice balance reconciliation, completed non-test quotation profitability.

Conservative decisions: unmatched receipts require review; no live spend or bank transfer; monthly projected commitment uses 31 days. Existing historical growth ledger needs review, not automatic rewriting.

Outstanding: validate FreeAgent snapshot fields and pagination with sandbox, invoice creation and explicit linking, bank explanation matching, CRM paid-stage sync, multi-visit completion, all campaign writers sharing transaction locks, actual daily platform spend time series, VAT/tax validation, attribution and live Meta/Google integration. Profitability is still an estimate, not statutory accounts. CI must pass before merge. No credentials or production actions performed.
