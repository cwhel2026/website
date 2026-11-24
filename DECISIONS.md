# Decisions log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11-24 | Monorepo `apps/api` + `apps/web` | Spec stack; single team velocity |
| 2025-11-24 | `create_all` + seed on API lifespan for dev | Docker not always available in agent; Alembic scaffold added |
| 2025-11-24 | Deterministic pricing in Python service | AI must not set prices |
| 2025-11-24 | Postcode district + town territory lookup | PostGIS columns deferred to Phase 2 scheduling |
| 2025-11-24 | JWT for dashboard Phase 1 | Fast path; cookies before prod |