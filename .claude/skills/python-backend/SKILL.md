---
name: python-backend
description: Backend conventions for this project (Python 3.12, FastAPI, SQLAlchemy 2, Pydantic, Alembic, Postgres) with a strict controller → service → DAO → model layering. Use whenever creating or editing anything under backend/, including the data pipeline.
---

# Python backend

Stack: Python 3.12, FastAPI, SQLAlchemy 2.0 (typed `Mapped[...]`), psycopg 3, Alembic,
pydantic-settings, pytest, ruff. Managed with uv (`uv add`, `uv run`). Never use pip directly.

## Folder structure

```
backend/
  pyproject.toml, uv.lock, alembic.ini, alembic/
  app/
    main.py            # create_app(): middleware, exception handlers, routers
    core/              # config.py (settings from env), database.py (engine, session, get_db), exceptions.py
    models/            # OBJECT LAYER (entities): SQLAlchemy ORM classes = tables
    schemas/           # OBJECT LAYER (transfer objects): Pydantic request/response models
    dao/               # DATA ACCESS: one DAO per model; queries only
    services/          # BUSINESS LOGIC: rules, calculations, transactions
    controllers/       # HTTP LAYER: FastAPI routers, one module per resource
    dependencies.py    # Depends() providers that build services
  pipeline/            # data download, cleaning, ML and index building (batch jobs)
    download/  clean/  features/  model/  index/  load.py
  tests/               # unit tests per layer + API tests
```

## Layer rules (dependencies only point downward)

```
controllers  →  services  →  dao  →  models
     └────────── schemas ──────────┘       (pipeline → services/dao to load results)
```

| Layer | Does | Never does |
|---|---|---|
| controllers | Parse request, call one service method, return a schema | SQL, business rules, `session.commit()` |
| services | Validation, calculations, orchestration, `commit()` / `rollback()` | Build HTTP responses, raise `HTTPException` |
| dao | `select`/`insert`/`update`/`delete`, `flush()` | `commit()`, business rules |
| models | Columns, relationships, constraints | Logic |
| schemas | Field types and validation; `XRead` uses `from_attributes=True` | DB access |

- Services raise domain exceptions from `core/exceptions.py` (NotFoundError, ConflictError, ...);
  `main.py` maps them to HTTP status codes.
- Controllers get services via `Depends` from `dependencies.py`, never DAOs directly.
- Every endpoint declares `response_model`. Never return ORM objects unvalidated.
- Register every model in `models/__init__.py` so Alembic autogenerate sees it.
- Schema changes go through Alembic migrations only (`alembic revision --autogenerate`).
  Never call `create_all()` in app code.

## Conventions
- snake_case files, singular per resource: `tract.py`, `tract_dao.py`, `tract_service.py`,
  `tract_controller.py`.
- Full type hints; `X | None` not `Optional[X]`. Config only from environment variables.
- Pipeline steps are idempotent functions with a CLI entry: `uv run python -m pipeline.<step>`.
- Tests: pytest, one file per service/controller. API tests use FastAPI TestClient with the
  test database. `uv run pytest` and `uv run ruff check .` must pass before merging.
