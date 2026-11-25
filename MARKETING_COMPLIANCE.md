# Marketing compliance (UK)

## Lawful basis

- **B2B corporate subscribers** — outreach drafts may use **legitimate interests** with documented balancing test; stored on `commercial_prospects.lawful_basis`.
- **Individuals / sole traders** — treated as personal subscribers under PECR; email/SMS marketing requires consent unless soft-opt-in rules clearly apply (not assumed by default).

## Outreach safeguards (implemented)

- Opt-out flag on prospects; suppressed messages cannot be drafted for ineligible records.
- No automated external send — status `pending_approval` until owner approves and mail provider is configured.
- Identification and unsubscribe line in draft template (`outreach_compliance.py`).
- Stop follow-ups on reply/opt-out (status enums; full automation when send path added).

## Customer review requests

- After job completion workflows must not incentivise positive-only reviews or selective requests (implement when GBP integration live).

## Data retention

- Prospect evidence JSON retains source metadata; deletion requests should remove or anonymise contact fields while keeping suppression keys.

## Email authentication

Before live commercial email, configure **SPF**, **DKIM**, and **DMARC** on the sending domain; document alignment in DNS provider.

## Advertising

- All spend gated by `marketing_budget_policies` and Approvals.
- Never claim campaigns are live without platform confirmation (`LIVE` vs `LIVE_SIMULATED` campaign status).