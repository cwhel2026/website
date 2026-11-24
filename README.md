# Revive My Drive

Regional Business Operating System

**Railway:** set each service **Root Directory** to `apps/web` or `apps/api` (not the repo root). See [DEPLOYMENT.md](./DEPLOYMENT.md).

Autonomous business management platform for a North West England exterior surface restoration company (headquarters: Burscough, Lancashire).

**Phase 1 (this repository state)** delivers the foundation: monorepo architecture, PostgreSQL/PostGIS-ready API, configurable territories, CRM, pricing engine, instant quotations, public website shell, and private dashboard shell.

## Repository layout

| Path | Purpose |
|------|---------|
| `apps/api` | Python FastAPI backend, SQLAlchemy models, pricing engine, seeds |
| `apps/web` | Next.js public site + business dashboard |
| `docker-compose.yml` | PostGIS + Redis for local development |
| `docs/*.md` | Architecture, roadmap, implementation status |

## Quick start (local)

### 1. Database

```bash
docker compose up -d db
cp .env.example .env
```

### 2. API

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

On first start the API creates tables and seeds territories A–I, services, default pricing profile, and an owner account from environment variables.

Default admin (override in `.env`):

- Email: `admin@revivemydrive.co.uk`
- Password: see `DEFAULT_ADMIN_PASSWORD` in `.env.example`

### 3. Web

```bash
cd apps/web
npm install
export NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) for the public site and [http://localhost:3000/dashboard/login](http://localhost:3000/dashboard/login) for the control centre.

## Tests

```bash
cd apps/api && source .venv/bin/activate && pytest -q
cd apps/web && npm run build
```

CI runs both on GitHub Actions (`.github/workflows/ci.yml`).

## What is implemented (Phase 1)

- **Territories**: Nine configurable regions with towns and postcode districts (API + dashboard view).
- **CRM**: Customers, properties, enquiries, pipeline stages, email deduplication.
- **Pricing**: Versioned profile and rules; deterministic quotation engine with minimum job, travel, VAT, margin checks.
- **Quotations**: Public instant quote API with section areas and stored calculation JSON.
- **Auth**: JWT login for owner/admin dashboard routes.
- **Website**: Homepage, services, regional landing pages, instant quote, legal placeholders, gallery empty state.

## Not implemented yet

See `IMPLEMENTATION_STATUS.md` for Phase 2+ (scheduling, weather, AI agents, FreeAgent, marketing APIs, mobile field ops, etc.). No live integrations are connected or claimed as complete.

## Documentation

- `ARCHITECTURE.md` — system design
- `ROADMAP.md` — phased delivery
- `BUSINESS_RULES.md` — operational rules (two-stage restoration, margins)
- `TERRITORIES.md` — territory model
- `INTEGRATIONS.md` — planned vs verified integrations
- `SECURITY.md` — Phase 1 security notes
- `DEPLOYMENT.md` — Railway/Docker notes
- `TESTING.md` — test strategy
- `IMPLEMENTATION_STATUS.md` — honest completion tracker
- `DECISIONS.md` — architecture decisions log