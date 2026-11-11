#!/usr/bin/env bash
# Copy the loaded `housing` data into `housing_test` so API tests run on real data.
# The test database is migrated to the same Alembic head first, then emptied and refilled
# (data only). Usage: scripts/seed_test_db.sh   (database must be running: scripts/db.sh start)
set -euo pipefail

PG=${PG_BIN:-/Library/PostgreSQL/18/bin}
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT=5544
SRC=housing
DST=housing_test
DUMP=/tmp/housing_data_$$.dump

(cd "$ROOT/backend" && DATABASE_URL="postgresql+psycopg://postgres@localhost:$PORT/$DST" \
  uv run alembic upgrade head >/dev/null)

TABLES=$("$PG/psql" -h localhost -p "$PORT" -U postgres -d "$DST" -tAc \
  "SELECT string_agg(quote_ident(tablename), ', ') FROM pg_tables
   WHERE schemaname = 'public' AND tablename <> 'alembic_version'")
"$PG/psql" -h localhost -p "$PORT" -U postgres -d "$DST" -q -c "TRUNCATE $TABLES CASCADE"

"$PG/pg_dump" -h localhost -p "$PORT" -U postgres -d "$SRC" --data-only -Fc \
  --exclude-table=alembic_version -f "$DUMP"
"$PG/pg_restore" -h localhost -p "$PORT" -U postgres -d "$DST" --data-only \
  --disable-triggers --single-transaction "$DUMP"
rm -f "$DUMP"
echo "seeded $DST from $SRC"
