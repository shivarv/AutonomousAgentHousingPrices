"""Load DATA_SOURCES.md into the data_sources table (idempotent upsert).

Run: uv run python -m pipeline.load_sources
"""

import sys

from app.core.database import get_session_factory
from app.dao.data_source_dao import DataSourceDao
from app.services.data_source_service import DataSourceService
from pipeline.sources import DATA_SOURCES_MD, parse


def main() -> int:
    rows = parse(DATA_SOURCES_MD.read_text())
    with get_session_factory()() as session:
        n = DataSourceService(DataSourceDao(session)).sync_from_rows(rows)
    print(f"data_sources: {n} rows upserted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
