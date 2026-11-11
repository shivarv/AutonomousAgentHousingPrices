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
