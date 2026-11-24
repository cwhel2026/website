# Territories

Territories are **data-driven** (`territories`, `territory_localities`, `postcode_districts`).

## Resolution order

1. Match UK outward postcode district on `postcode_districts.district`.
2. Else match `town` against `territory_localities.name` (case-insensitive).

## Configuration (admin API)

- `PATCH /api/v1/territories/{id}` — minimum job value, travel rates, active flag.
- `POST /api/v1/territories/postcode-districts` — add district mapping without deploy.

## Seed regions

Codes **A–I** match the master specification (West Lancashire through Warrington). Full town and district lists are in `apps/api/app/seeds/bootstrap.py`.