# Massachusetts Housing Need & Site Finder

A statewide tool for city planners and housing nonprofits. It covers all 351 cities and towns,
the 1,620 census tracts, 14 counties, 11 Continuums of Care (CoCs) and Boston's neighbourhoods,
and answers two questions:

1. **The picture.** How many people are homeless or at risk, where is the affordable-housing
   shortage, and which places are suitable for building new homes? The answer is given as
   statistics (`reports/STATISTICS.md`, the Overview page) and as a ranked list of 40,873
   screened candidate sites (`reports/candidate_sites.csv`).
2. **The site explorer.** An interactive map. Press "Show best location", or drag the pin
   anywhere, to see the estimated number of people experiencing homelessness, at-risk
   households, and the shortage or surplus of affordable homes. The map shows these for the
   area under the pin (tract, Boston neighbourhood, town, county or CoC), which you can grow
   into a "benefit area", or for three distance rings.

Every figure comes from a downloaded public dataset (`DATA_SOURCES.md`) and is shown with its
source and year. Official homelessness counts exist only per CoC (HUD Point-in-Time count).
Every homelessness figure below CoC level is a modelled **estimate** and is labelled that way
in the data, the API, the app and the reports. The method and its limits are in
`reports/REPORT.md` 3.2 and on the app's "About the estimates" page. The app never shows the
locations of individual people, and it never publishes domestic-violence shelter locations.

Results and methods are in `reports/REPORT.md`. Decisions are recorded in `DECISIONS.md` and
known gaps in `BLOCKERS.md`.

## Layout
```
backend/    one uv project: FastAPI app (app/: controllers -> services -> DAOs -> models/schemas),
            data pipeline (pipeline/), Alembic migrations (alembic/), tests (tests/)
frontend/   React 19 + TypeScript + Vite + Tailwind v4 (feature folders in src/features/)
scripts/    db.sh (local Postgres), seed_test_db.sh (copy data into housing_test), validate.py
reports/    REPORT.md, STATISTICS.md, model_metrics.json, top_tracts.csv, candidate_sites.csv,
            data_audit.md, sensitivity checks, charts
data/       raw/ interim/ processed/ pg/   (git-ignored; about 3.2 GB after a full rebuild, incl. the database)
compose.yaml, backend/Dockerfile, frontend/Dockerfile
```

## Run locally

Requirements: Python 3.12 with [uv](https://docs.astral.sh/uv/), Node 22 with npm, and the
PostgreSQL 18 binaries. `scripts/db.sh` looks for them in `/Library/PostgreSQL/18/bin`; set
`PG_BIN` to use another location. No PostGIS is needed. All spatial work runs in Python
(shapely, pyproj, geopandas), and geometry is stored as GeoJSON in `jsonb` columns.

```bash
scripts/db.sh init && scripts/db.sh start     # private Postgres on port 5544: housing, housing_test
(cd backend && uv sync && uv run alembic upgrade head)
# ...load the data (next section), then:
(cd backend && uv run uvicorn app.main:app --port 8000)      # API on http://localhost:8000/api
(cd frontend && npm ci && npm run dev)                        # app on http://localhost:5173
```
In development, Vite forwards `/api` to port 8000. API documentation is served at
`http://localhost:8000/docs`.

Checks:
```bash
scripts/seed_test_db.sh                       # copy the loaded data into housing_test
(cd backend && uv run pytest && uv run ruff check .)
(cd frontend && npm run build && npm run lint)
uv run --project backend python scripts/validate.py     # end-to-end acceptance checks
scripts/db.sh stop
```

## Rebuild the data from scratch

Every step is idempotent and runs from `backend/` (`cd backend`). Downloads go to `data/raw/`
untouched, along with a manifest of URL, date and sha256. That folder is then treated as
read-only. Derived files go to `data/interim/` and `data/processed/`. The ACS download needs a
free Census API key in the `CENSUS_API_KEY` environment variable. Never write the key to a file.

```bash
uv run alembic upgrade head
# 1. Download (about 2 GB) and register the sources
uv run python -m pipeline.download              # every source module (or pipeline.download.<name>)
uv run python -m pipeline.sources               # regenerates DATA_SOURCES.md from the manifests
uv run python -m pipeline.load_sources          # data_sources table
# 2. Clean
uv run python -m pipeline.clean                 # geography, ACS, PIT/HIC, context layers
uv run python -m pipeline.clean.parcels         # assessor parcels (large; several minutes)
# 3. Tract features (written to data/processed/*.parquet)
uv run python -m pipeline.features.affordability    # CHAS affordable gap
uv run python -m pipeline.features.land_value       # land value per sq ft
uv run python -m pipeline.features.homeless_estimate   # modelled ESTIMATES (sum to CoC counts)
uv run python -m pipeline.index.need_index          # Housing Need Index
# 4. Load into Postgres and aggregate to town/county/CoC/neighbourhood/state
uv run python -m pipeline.load
uv run python -m pipeline.features.aggregate
# 5. Sensitivity checks and need reports
uv run python -m pipeline.features.homeless_sensitivity
uv run python -m pipeline.index.sensitivity
uv run python -m pipeline.index.report          # top_tracts.csv, municipality_need.csv
# 6. Home-value model (70/15/15 split is saved once and reused; the test split is scored once)
uv run python -m pipeline.model.dataset
uv run python -m pipeline.model.home_value
uv run python -m pipeline.model.artifacts       # model_metrics.json, importances, model_runs row
# 7. Candidate sites
uv run python -m pipeline.sites.screen
uv run python -m pipeline.sites.features
uv run python -m pipeline.sites.score
uv run python -m pipeline.sites.load            # site_candidates, candidate_sites.csv
# 8. Reports
uv run python -m pipeline.audit                 # data_audit.md
uv run python -m pipeline.stats_report          # STATISTICS.md
```
If a source cannot be downloaded, the step logs the problem and the gap is documented in
`BLOCKERS.md`. No value is ever invented to fill it.

## Docker (untested here)
`compose.yaml`, `backend/Dockerfile` and `frontend/Dockerfile` define the whole stack:
- `db`: Postgres 18, with a healthcheck.
- `backend`: the API. It applies the Alembic migrations, then starts uvicorn on port 8000.
- `frontend`: nginx on port 8080. It serves the Vite build and forwards `/api` to the backend.

> These files were written on a machine without Docker and have **not been built or run**.
> Only static checks pass (`backend/tests/test_docker_files.py`: the YAML parses, every build
> context, Dockerfile, COPY source and mount exists, and the services are wired as intended).

```bash
docker compose up --build            # http://localhost:8080
# The database starts empty. Run the rebuild steps above with the pipeline service,
# which uses the backend image with data/, reports/ and DATA_SOURCES.md mounted, e.g.:
CENSUS_API_KEY=... docker compose --profile pipeline run --rm pipeline python -m pipeline.download
docker compose --profile pipeline run --rm pipeline python -m pipeline.load
```
Set `POSTGRES_PASSWORD` in your shell (or in a git-ignored `.env`) for anything beyond local use.

## Data and licences
All sources are public and free. Licences and terms are listed per dataset in
`DATA_SOURCES.md`. The app uses OpenStreetMap tiles and the US Census Geocoder, so it needs no
map API keys.
