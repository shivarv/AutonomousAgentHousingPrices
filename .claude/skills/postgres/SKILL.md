---
name: postgres
description: How this project runs and uses PostgreSQL 18 (a private local instance inside the project, Alembic migrations, schema conventions, no PostGIS). Use for anything touching the database, DATABASE_URL, migrations or SQL.
---

# PostgreSQL

## Local database (no password, nothing installed system-wide)
PostgreSQL 18 binaries are at `/Library/PostgreSQL/18/bin` (initdb, pg_ctl, psql, createdb).
Run a private instance whose data lives in `data/pg/` (git-ignored), on port **5544**:

```bash
PG=/Library/PostgreSQL/18/bin
$PG/initdb -D data/pg -U postgres --auth=trust -E UTF8      # first time only
$PG/pg_ctl -D data/pg -l data/pg.log -o "-p 5544 -k /tmp" start
$PG/createdb -h localhost -p 5544 -U postgres housing
$PG/createdb -h localhost -p 5544 -U postgres housing_test
$PG/pg_ctl -D data/pg stop                                   # at the end
```

Wrap these in `scripts/db.sh {init|start|stop|status}` (idempotent) and use it everywhere.
`DATABASE_URL=postgresql+psycopg://postgres@localhost:5544/housing` (put the default in
`backend/app/core/config.py`; tests use `housing_test`). Never use port 5432: it belongs to
another Postgres on this machine whose password we don't have.

For Docker/production, compose.yaml uses the official `postgres:18` image instead; the app only
sees DATABASE_URL, so nothing else changes.

## Schema conventions
- Tables plural snake_case (`tracts`, `tract_metrics`, `properties`, `data_sources`).
- Primary keys: `id` bigint identity, or the natural key where stable (`geoid` text for tracts).
- Money as `numeric(12,2)`; rates/shares as `double precision` 0-1; years as smallint.
- Every metric table has `source_id` → `data_sources.id` so each number is traceable.
- Index foreign keys and common filters (geoid, year, neighbourhood).
- Geometry: PostGIS is NOT installed. Store tract shapes as GeoJSON in a `jsonb` column
  (simplified to keep responses small); do spatial work in geopandas inside the pipeline.
- Use a naming convention on `MetaData` so constraint names are stable for Alembic.

## Migrations
- Only via Alembic: edit models → `uv run alembic revision --autogenerate -m "..."` →
  review the file → `uv run alembic upgrade head`.
- Never edit a migration that has been merged to main; add a new one.

## Queries
- Through DAOs with SQLAlchemy 2.0 `select()`; never string-built SQL with user input.
- Bulk loads in the pipeline: `session.execute(insert(Model), rows)` in batches of ~5,000.
- Avoid N+1: use `selectinload` / joins for related data.
