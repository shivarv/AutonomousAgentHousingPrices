#!/usr/bin/env bash
# Copy the loaded local `housing` database (port 5544) into a hosted Postgres for deployment.
# Usage: TARGET_DATABASE_URL='postgresql://user:pass@host/db?sslmode=require' scripts/publish_db.sh
# The URL is read from the environment so it never lands in shell history or logs.
# The dump is written to data/export/ (git-ignored). Existing tables in the target are replaced.
set -euo pipefail

PG=${PG_BIN:-/Library/PostgreSQL/18/bin}
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DUMP="$ROOT/data/export/housing.dump"

if [ -z "${TARGET_DATABASE_URL:-}" ]; then
  echo "set TARGET_DATABASE_URL to the hosted database URL (postgresql://...)" >&2
  exit 1
fi
# libpq does not understand SQLAlchemy's driver suffix
TARGET=${TARGET_DATABASE_URL/postgresql+psycopg:\/\//postgresql://}

mkdir -p "$(dirname "$DUMP")"
echo "dumping local housing database -> $DUMP"
"$PG/pg_dump" -h localhost -p 5544 -U postgres -d housing \
  --format=custom --no-owner --no-acl --file "$DUMP"
ls -lh "$DUMP"

echo "restoring into the target database (replacing existing tables)"
"$PG/pg_restore" --dbname "$TARGET" --clean --if-exists --no-owner --no-acl \
  --single-transaction "$DUMP"

echo "row counts in the target:"
"$PG/psql" "$TARGET" -Atc "select 'tracts', count(*) from tracts
  union all select 'tract_metrics', count(*) from tract_metrics
  union all select 'site_candidates', count(*) from site_candidates
  union all select 'homelessness_counts', count(*) from homelessness_counts"
