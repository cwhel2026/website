# Phase 22 execution status

This change is a bounded implementation, not completion of the requested AI business operating system.

## Implemented

Trusted Telegram update identity reaches the provider's structured tools. Employees can enqueue campaign preparation, finance evidence reviews and operations evidence reviews. A five-minute worker processes durable tasks with role gates, row locks, bounded retries, transaction rollback, audit events and completion/failure notifications. Duplicate tool calls within the same update reuse the task. Campaign drafts use existing RegionalCampaign records. Completed work and budget/scenario evidence appear on the existing command centre and marketing pages, refreshing every 15 seconds.

Campaign planning applies overall daily/weekly/monthly limits, Meta limits, existing commitments, recorded spend and the saved safety buffer. Zero limits block allocations. Cumulative campaign counters are explicitly provisional, not incorrectly labelled as weekly billing. Scenario forecasts separate demand from fulfilment capacity and add qualified leads and break-even economics where explicit assumptions exist. Missing finance evidence never becomes spending authority. The provider no longer replaces every campaign answer with a fixed report.

The configured AI model is retained. No database migration is needed.

## Evidence and verification

Regression tests cover a £150 draft with a 5% buffer, duplicate execution, dashboard API readback, unknown bank evidence, unavailable integrations, capacity constraints, conflicting limits, rollback after a campaign write, bounded retries, role denial and emergency stop. A mocked-provider Telegram webhook test covers owner authentication, tool dispatch, duplicate update handling, worker execution and dashboard API readback. Tests use a real SQLite database for these local workflow checks; they do not certify PostgreSQL concurrency or a live Telegram/model session.

Meta documentation reviewed on 28 November 2026:
- https://developers.facebook.com/docs/graph-api/reference/ad-campaign/delivery_estimate/
- https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-delivery-estimate/
- https://developers.facebook.com/docs/graph-api/reference/targeting/
- https://developers.facebook.com/documentation/ads-commerce/marketing-api

A read-only existing-ad-set estimate tool distinguishes monthly eligible audience bounds from campaign reach, and reports unready estimates as unavailable. It does not invent delivery curves or audience IDs.

## Outstanding acceptance blockers

- Full campaign/ad-set/creative/ad publication and resumable external-write reconciliation remain incomplete. The existing launch adapter rejects live publication. Saved drafts remain simulation-only. No ads were published by this change.
- Finance and operations handlers save evidence reviews; they do not yet implement autonomous reconciliation, invoice/receipt workflows, quote or scheduling mutations, or dependency graphs.
- Campaign department reviews are deterministic evidence checks, not independent AI colleague execution. Research remains stored/database evidence; live competitor discovery and outcome-learning are not implemented here.
- Current campaign scenarios are explicitly hypothetical. Historical conversion calibration, platform daily delivery forecasts, attributed contribution, verified bank balances and dated spend ledgers remain outstanding.
- Material ordering, external messages, tax filing and money transfers are not enabled. Full Telegram approval/publication workflow is not implemented.
- Meta token/app permissions/ad account/page/creative assets, consented Pixel/CAPI setup, FreeAgent OAuth, bank reconciliation evidence and production worker health require authenticated verification.
- Production /health initially returned HTTP 200 but git_commit=unknown; configuration now supports Railway's commit environment variable. A healthy response alone does not prove deployment identity or end-to-end acceptance.

Do not describe CI success as completion of Phase 22.
