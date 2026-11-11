"""Record rows dropped during cleaning so nothing disappears silently.

Each cleaning step calls ``record_drop``; entries go to data/processed/dropped_rows.json
(replaced per step on rerun) and are summarised in reports/load_summary.md by pipeline.load.
"""

from __future__ import annotations

import json
import logging

from pipeline.paths import PROCESSED_DIR

DROPS_FILE = PROCESSED_DIR / "dropped_rows.json"
log = logging.getLogger("pipeline.drops")


def _read() -> dict[str, dict[str, int]]:
    return json.loads(DROPS_FILE.read_text()) if DROPS_FILE.exists() else {}


def reset(step: str) -> None:
    data = _read()
    data.pop(step, None)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DROPS_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))


def record_drop(step: str, reason: str, count: int) -> None:
    log.info("%s: dropped %d rows (%s)", step, count, reason)
    data = _read()
    data.setdefault(step, {})[reason] = int(count)
    DROPS_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))


def all_drops() -> dict[str, dict[str, int]]:
    return _read()
