# Project: Massachusetts Housing Need & Impact Map

## Goal
Build a working product that shows housing costs and housing need across **the whole state of
Massachusetts**: all 351 cities and towns and every census tract in the state. Boston and the
Greater Boston area are the most important to get right (most people and most need), but the
data, index, API and map must cover the entire state. Users must be able to filter by county
and municipality.

Deliverables:
1. A data pipeline that downloads real public data, cleans it and loads it into Postgres.
2. A home-value prediction model.
3. A Housing Need Index (0-100) for every census tract.
4. A ranked list of tracts where new affordable housing would have the highest impact.
5. A FastAPI backend serving all of this.
6. A React web app with an interactive map, tract details, rankings and data sources.
7. Docker files to run the whole product, and a written report.

## Audience
City planners and housing nonprofits. Every number must be trustworthy and traceable.

## How to work (details in CLAUDE.md and .claude/skills/)
- Branch per task, split into items, commit per item, merge to main when checks pass
  (skill: git-task-workflow).
- Backend layering controller → service → DAO → model/schema (skill: python-backend).
- Database: private local Postgres 18 on port 5544 (skill: postgres).
- Frontend: modular feature folders, Tailwind v4 (skills: react, tailwind, frontend-design).
- Docker files (skills: docker-project-foundations, docker-compose-patterns,
  docker-build-strategies). Docker isn't installed here: write the files, don't run them.

## Target layout
```
backend/    FastAPI app (app/) + data pipeline (pipeline/) + alembic/ + tests/   (one uv project)
frontend/   React + TypeScript + Vite + Tailwind
scripts/    db.sh (local Postgres), validate.py
reports/    REPORT.md, model_metrics.json, top_tracts.csv, data_audit.md, charts
data/       raw/ interim/ processed/ pg/   (git-ignored)
compose.yaml, backend/Dockerfile, frontend/Dockerfile
```

## Data sources (try in order; log failures in BLOCKERS.md and move on)
| Need | Primary source | Fallback |
|---|---|---|
| Tract, county and municipality boundaries | Census TIGER/Line (state FIPS 25, latest year) | MassGIS municipal boundaries |
| Rent burden, income, poverty, overcrowding, tenure, population | ACS 5-year via api.census.gov for every MA tract (env var CENSUS_API_KEY) | data.census.gov bulk download |
| Property values + features (statewide) | MassGIS Standardized Assessors' Parcels (assessor tables for all MA towns; use attribute tables, skip parcel geometry to save space) | Analyze Boston property assessment (Boston only) |
| Value/rent trends | Zillow Research ZHVI and ZORI (all MA ZIPs) | Redfin Data Center |
| Evictions | MA Trial Court housing court filings (statewide) | Eviction Lab |
| Homelessness (CoC level ONLY) | HUD Point-in-Time counts for every Massachusetts Continuum of Care | HUD Exchange reports |
| Student homelessness | MA DESE homeless student counts for every school district | — |
| Shelters, subsidised housing | HUD LIHTC database, HUD Picture of Subsidized Households (MA), MA EOHLC/CHAPA public listings | Analyze Boston |
| ZIP to tract mapping | HUD USPS ZIP-tract crosswalk | Census ZCTA-to-tract relationship file |

Data size: statewide parcel data is large. Keep only residential parcels and the columns the
model needs; drop geometry; stay within the 8 GB data budget.

## Tasks (in order; each task = one branch; split into items before starting)

### Phase 1 – Foundations
- [ ] Repo skeleton: folders above, root README stub, .gitignore additions.
- [ ] scripts/db.sh (init/start/stop/status) for the local Postgres on port 5544; create
      databases `housing` and `housing_test`.
- [ ] Backend skeleton: uv project (Python 3.12), FastAPI app with core/, models/, schemas/,
      dao/, services/, controllers/, dependencies.py; /api/health endpoint; Alembic configured;
      pytest + ruff passing.
- [ ] Frontend skeleton: Vite React TS, Tailwind v4, react-router, react-query, @/ alias,
      layout shell; build and lint passing.

### Phase 2 – Data collection (backend/pipeline/download/)
- [ ] One idempotent download module per source, saving untouched files to data/raw/<source>/.
- [ ] DATA_SOURCES.md entries for every dataset, plus a `data_sources` table loaded from it.
- [ ] reports/data_audit.md: rows, years, geography, missing-value rates, known issues.

### Phase 3 – Database schema and loading
- [ ] Models + Alembic migration: data_sources, counties, municipalities, tracts (geoid, name,
      county, municipality, GeoJSON), tract_metrics (one row per tract per metric, with
      source_id and year), properties, shelters_subsidised, homelessness_counts (per CoC, with
      the municipalities each CoC covers), model_runs.
- [ ] Pipeline clean/ + load.py: cleaned data into the tables via DAOs. Join ZIP data to tracts
      via the crosswalk, weighted by residential share (record in DECISIONS.md).
- [ ] Tests: tract count matches the statewide TIGER file, all 351 municipalities and 14
      counties present, no duplicate geoids, every metric row has a source, dropped rows
      logged with reasons.

### Phase 4 – Home-value model (backend/pipeline/model/)
- [ ] Residential parcels statewide. Split 70/15/15 stratified by county; save the test split
      once and never tune on it.
- [ ] Baseline: municipality median value. Record MAE and MAPE, overall and per county.
- [ ] Linear regression, then LightGBM, tuned on validation only.
- [ ] Target: beat baseline MAPE by >= 25% on test. Save model, reports/model_metrics.json,
      feature importances, error-by-county chart, and a model_runs row.

### Phase 5 – Housing Need Index (backend/pipeline/index/)
- [ ] Components scaled 0-1: renters paying >30% of income, >50%, eviction filing rate,
      poverty rate, overcrowding rate, 5-year rent growth, distance to nearest shelter or
      subsidised unit.
- [ ] Equal weights to start (justify changes in DECISIONS.md); store index and components.
- [ ] Sensitivity check with 3 alternative weightings; report top-20 stability.
- [ ] Impact ranking: need index x renter households, adjusted down for existing subsidised
      units. reports/top_tracts.csv (top 50 statewide) plus top 10 per county; stored in the DB.
- [ ] Municipality summary: population-weighted need index per city/town.

### Phase 6 – Backend API (controllers → services → DAOs)
- [ ] GET /api/tracts?county=&municipality= (GeoJSON FeatureCollection with index + key
      metrics; statewide must stay fast: simplified geometry, cached response)
- [ ] GET /api/tracts/{geoid} (all metrics with source and year)
- [ ] GET /api/municipalities and GET /api/counties (summaries for filters and the overview)
- [ ] GET /api/rankings?limit=50&county= (statewide or per county)
- [ ] GET /api/homelessness (counts per CoC by year, with covered municipalities, labelled as
      CoC-level)
- [ ] GET /api/model/metrics and GET /api/sources
- [ ] API tests for every endpoint against housing_test, including 404 and validation errors.

### Phase 7 – Frontend (feature modules)
- [ ] features/map: statewide Leaflet choropleth (opens on all of Massachusetts) with county and
      municipality filters that zoom the map, layer switcher (Need Index, median value, rent
      burden, eviction rate), legend, shelter/subsidised markers, click to select a tract.
- [ ] features/tracts: detail panel listing every index component with its source and year.
- [ ] features/rankings: sortable table (statewide top 50, or per county) linked to the map.
- [ ] features/municipalities: city/town summary view with its tracts.
- [ ] features/homelessness: per-CoC panel, clearly labelled as not tract-level.
- [ ] pages: Map (home), Rankings, Methodology & sources, About the model.
- [ ] Loading, error and empty states everywhere; responsive down to phone width.

### Phase 8 – Docker
- [ ] backend/Dockerfile (multi-stage, uv, non-root), frontend/Dockerfile (build + static
      server), compose.yaml (postgres:18 with healthcheck, backend runs migrations then
      uvicorn, frontend), .dockerignore files. Docker isn't installed here: validate the YAML
      parses and paths exist; note in README that it's untested.

### Phase 9 – Report and final checks
- [ ] reports/REPORT.md: question, data, methods, results, limitations, next steps.
- [ ] README.md: what it is, how to run (local and Docker), how to rebuild data from scratch.
- [ ] scripts/validate.py passes (see Definition of done).

## Definition of done
All tasks merged into main AND `uv run --project backend python scripts/validate.py` exits 0.
validate.py checks that:
- every metric in tract_metrics has a source in data_sources, and DATA_SOURCES.md lists them all;
- Need Index values are within 0-100 with no missing values (or each gap documented);
- reports/model_metrics.json exists; the test result meets the target, or REPORT.md says
  plainly that it doesn't (never change the target);
- reports/REPORT.md and reports/top_tracts.csv exist and aren't empty;
- backend `pytest` and `ruff check` pass; frontend `npm run build` and `npm run lint` pass;
- the database covers all MA tracts (statewide TIGER count), 351 municipalities, 14 counties;
- git: no unmerged task/* branches, working tree clean (and, in PR mode, no open PRs).
Then write DONE to the file STATUS (on main).

## Out of scope
User accounts, paid data, scraping sites whose terms forbid it, tract-level homelessness
estimates, deploying anywhere.
