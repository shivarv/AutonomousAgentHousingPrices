# Massachusetts Housing Need & Site Finder

Statewide (all 351 cities and towns, every census tract, 14 counties) picture of homelessness,
housing risk and the affordable-housing shortage, plus a ranked list of candidate construction
sites and an interactive site explorer map.

> Work in progress. See `PLAN.md` for the full plan and `PROGRESS.md` for status.

## Layout
```
backend/    FastAPI app (app/) + data pipeline (pipeline/) + alembic/ + tests/
frontend/   React + TypeScript + Vite + Tailwind
scripts/    db.sh (local Postgres), validate.py
reports/    reports, statistics and charts
data/       raw/ interim/ processed/ pg/   (git-ignored)
```

## Data integrity
Every number comes from a downloaded public dataset (see `DATA_SOURCES.md`). Official
homelessness counts exist only per Continuum of Care (CoC); tract-level homelessness numbers
are modelled **estimates** and are labelled as such everywhere.

## Docker (untested here)
`compose.yaml`, `backend/Dockerfile` and `frontend/Dockerfile` run the whole stack: Postgres 18
(`db`, with a healthcheck), the API (`backend`: applies Alembic migrations, then uvicorn on
port 8000) and the web app (`frontend`: nginx on port 8080 serving the Vite build and
forwarding `/api` to the backend).

> These files were written on a machine without Docker and have **not been built or run**.
> Only static checks pass (`backend/tests/test_docker_files.py`: YAML parses, every build
> context, Dockerfile, COPY source and mount exists, services are wired as intended).

```bash
docker compose up --build            # http://localhost:8080
# The database starts empty. Load it with the pipeline (same image, data/ and reports/ mounted):
CENSUS_API_KEY=... docker compose --profile pipeline run --rm pipeline python -m pipeline.download
docker compose --profile pipeline run --rm pipeline python -m pipeline.load
```
Set `POSTGRES_PASSWORD` in your shell (or a git-ignored `.env`) for anything beyond local use.
