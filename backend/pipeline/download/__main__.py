"""Run every download module (idempotent). Usage: uv run python -m pipeline.download [name ...]"""

import logging
import sys

from pipeline.download import (
    acs,
    boundaries,
    chas,
    hud_pit_hic,
    massgis,
    shelters_evictions,
    subsidised,
    transit,
    zillow_crosswalk,
)
from pipeline.download.common import setup_logging

MODULES = {
    "boundaries": boundaries,
    "acs": acs,
    "chas": chas,
    "hud_pit_hic": hud_pit_hic,
    "subsidised": subsidised,
    "transit": transit,
    "zillow_crosswalk": zillow_crosswalk,
    "massgis": massgis,
    "shelters_evictions": shelters_evictions,
}


def main(names: list[str]) -> int:
    setup_logging()
    log = logging.getLogger("pipeline.download")
    failures = []
    for name in names or list(MODULES):
        log.info("== %s", name)
        try:
            MODULES[name].run()
        except Exception as exc:  # keep going: one failing source must not block the others
            log.error("%s failed: %s", name, exc)
            failures.append(name)
    if failures:
        log.error("failed sources: %s", ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
