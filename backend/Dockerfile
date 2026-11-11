# syntax=docker/dockerfile:1
# Backend image: FastAPI app + data pipeline + Alembic migrations (one uv project).
# Build context: backend/   (compose.yaml sets this).
# Untested here: Docker is not installed on the machine this was written on.

ARG PYTHON_VERSION=3.12

# --- Build stage: resolve the locked dependencies into /app/.venv with uv ---
FROM python:${PYTHON_VERSION}-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/srv/backend/.venv
WORKDIR /srv/backend

# Dependencies first (cached until pyproject.toml / uv.lock change); no dev tools in the image.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --locked --no-dev --no-install-project

# --- Runtime stage ---
FROM python:${PYTHON_VERSION}-slim AS runtime
LABEL org.opencontainers.image.source="https://github.com/shivarv/AutonomousAgentHousingPrices" \
      org.opencontainers.image.title="housing-backend"

RUN addgroup --system --gid 1001 app \
    && adduser --system --uid 1001 --ingroup app --home /srv app

# The pipeline resolves the project root as the parent of backend/ (pipeline/paths.py), so the
# code lives in /srv/backend and data/, reports/ and DATA_SOURCES.md are mounted under /srv.
WORKDIR /srv/backend
COPY --link --from=build --chown=1001:1001 /srv/backend/.venv /srv/backend/.venv
COPY --link --chown=1001:1001 app ./app
COPY --link --chown=1001:1001 pipeline ./pipeline
COPY --link --chown=1001:1001 alembic ./alembic
COPY --link --chown=1001:1001 alembic.ini pyproject.toml ./

ENV PATH="/srv/backend/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER 1001:1001
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2).status == 200 else 1)"]

# Apply migrations, then serve. DATABASE_URL comes from the environment (compose.yaml).
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]
