# Architecture

## Overview

Modular **monorepo** (not microservices):

1. **Next.js** (`apps/web`) — public marketing site, customer quote funnel, owner dashboard UI.
2. **FastAPI** (`apps/api`) — authoritative business logic, persistence, authentication.
3. **PostgreSQL + PostGIS** — primary datastore (territories, CRM, quotations, future geo scheduling).
4. **Redis** — reserved for Celery/queues (container defined; workers in Phase 2+).

AI agents and background integrations will call **typed REST services** on the API, not direct database access from the frontend.

## Principles

- **Deterministic rules** for pricing, tax, scheduling constraints, and safety (Phase 1: pricing).
- **AI recommends and coordinates** but does not override validated rules (agents: Phase 3+).
- **Configurable territories and pricing** without code deploys.
- **Audit-friendly quotation versions** (`quotation_calculations.breakdown_json`).

## Authentication

- Dashboard: JWT bearer tokens issued by `/api/v1/auth/login`.
- Phase 1 stores tokens in `localStorage` (upgrade to HTTP-only cookies before production hardening).

## Future components (named, not built)

- Celery workers for weather polling, briefings, sync jobs.
- S3-compatible private object storage for customer photos.
- AI orchestration layer with task queues and approval workflows.
- Mobile-first field operations PWA.