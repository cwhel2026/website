# Business rules (encoded and planned)

## Enforced in Phase 1 (code)

- Provisional quotations include disclaimer text.
- Minimum job charge and territory minimum applied in pricing engine.
- Travel cost: base + per-km × distance × 2 (round trip placeholder).
- VAT at configurable rate (default 20%).
- Contribution margin vs configurable minimum; `requires_approval` when margin fails or total ≥ £5000.
- Customer deduplication by email on enquiry/quote.

## Mandatory operational rules (Phase 2+ implementation)

- **Two-stage restoration**: washing then coating within 7 calendar days where product and weather allow.
- **Never** override manufacturer drying/temperature/rain constraints.
- **Do not** book washing without projected coating capacity.
- **Safety and existing commitments** before profit optimisation in scheduling.
- **No bank payments** from the system; advertising spend requires authorisation.