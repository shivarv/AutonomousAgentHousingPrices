#!/usr/bin/env bash
# Private local PostgreSQL 18 for this project (data in data/pg, port 5544, trust auth).
# Usage: scripts/db.sh {init|start|stop|status}
# All commands are idempotent. Databases: housing, housing_test.
set -euo pipefail

PG=${PG_BIN:-/Library/PostgreSQL/18/bin}
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data/pg"
LOG="$ROOT/data/pg.log"
PORT=5544
DATABASES=(housing housing_test)

is_initialised() { [ -f "$DATA/PG_VERSION" ]; }
is_running() { "$PG/pg_ctl" -D "$DATA" status >/dev/null 2>&1; }

init() {
  if is_initialised; then
    echo "already initialised: $DATA"
  else
    mkdir -p "$DATA"
    "$PG/initdb" -D "$DATA" -U postgres --auth=trust -E UTF8 >/dev/null
    echo "initialised: $DATA"
  fi
}

create_databases() {
  for db in "${DATABASES[@]}"; do
    if "$PG/psql" -h localhost -p "$PORT" -U postgres -d postgres -tAc \
        "SELECT 1 FROM pg_database WHERE datname='$db'" | grep -q 1; then
      echo "database exists: $db"
    else
      "$PG/createdb" -h localhost -p "$PORT" -U postgres "$db"
      echo "database created: $db"
    fi
  done
}

start() {
  is_initialised || init
  if is_running; then
    echo "already running on port $PORT"
  else
    "$PG/pg_ctl" -D "$DATA" -l "$LOG" -o "-p $PORT -k /tmp" -w start >/dev/null
    echo "started on port $PORT"
  fi
  create_databases
}

stop() {
  if is_initialised && is_running; then
    "$PG/pg_ctl" -D "$DATA" -m fast -w stop >/dev/null
    echo "stopped"
  else
    echo "not running"
  fi
}

status() {
  if ! is_initialised; then
    echo "not initialised"
  elif is_running; then
    echo "running on port $PORT"
  else
    echo "stopped"
  fi
}

case "${1:-}" in
  init) init ;;
  start) start ;;
  stop) stop ;;
  status) status ;;
  *) echo "Usage: $0 {init|start|stop|status}" >&2; exit 2 ;;
esac
