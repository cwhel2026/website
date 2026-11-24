# Implementation status

Last updated: 2025-11-24 (production quality recovery — stage 1).

Status legend: **Not started** · **Scaffolded** · **Implemented** · **Tested locally** · **Integration verified** · **Production verified** · **Blocked**

## Stage 1 (this run): Public site, quotations, deploy traceability

| Feature | Status | Evidence / limits |
|---------|--------|-------------------|
| Stock driveway photography (labelled, not fake projects) | **Tested locally** | `apps/web/public/media/stock/*`, `src/lib/media-assets.ts`, `BeforeAfterSlider` image comparison |
| Homepage & service page imagery | **Tested locally** | `(site)/page.tsx`, `service-page.tsx` |
| Media manifest & requirements | **Implemented** | `public/media/manifest.json`, dashboard checklist `dashboard/website/page.tsx` |
| Default Next.js SVG template assets | **Implemented** | Removed from `apps/web/public/` |
| Anonymous provisional quotation API | **Tested locally** | `POST /api/v1/quotations/provisional`, `quotation_workflow.py`; tests `test_quotation_workflow.py` |
| Customer quotation submit + idempotency | **Implemented** | `POST /api/v1/quotations/submit`, `quotation_persist.py`, `quotation_idempotency` model |
| Quote wizard (no fake customer on estimate) | **Tested locally** | `quote-wizard.tsx` → provisional then submit |
| Build version identifiers | **Implemented** | Web `/api/version`, API `/health` `git_commit`; `DEPLOYMENT_VERIFICATION.md` |
| Railway deploy verification doc | **Implemented** | `DEPLOYMENT_VERIFICATION.md` |
| Production deploy matches `main` | **Blocked** | Requires owner to confirm Railway root dirs + redeploy; compare `/api/version` SHA |

**Tests executed (local):** `pytest apps/api/tests/test_quotation_workflow.py` (3 passed); full API suite pending CI; `npm run build` for web.

## Priorities 4–10 (not started in this run)

| Area | Status | Notes |
|------|--------|-------|
| Genuine AI assistant (OpenAI/tools) | **Scaffolded** | `assistant_brain.py` regex-based |
| Marketing intelligence (live APIs) | **Scaffolded** | Fixed slot assumptions; adapters not live |
| Live UK weather provider | **Not started** | `weather_engine.py` simulated |
| Celery/Redis automation workers | **Not started** | |
| FreeAgent / Mettle OAuth sync | **Scaffolded** | FreeAgent returns not-implemented |
| Alembic real migrations | **Scaffolded** | Empty initial revision |
| E2E production visual verification | **Not started** | Playwright smoke only |

## Retained working capabilities

Pricing engine, territories, dashboard routes, finance scaffolds, rate limits, health/readiness — unchanged unless listed above.