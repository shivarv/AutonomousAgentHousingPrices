"""Run every cleaning step in order: uv run python -m pipeline.clean"""

import logging

from pipeline.clean import acs, context, geography, homelessness

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    for step in (geography, acs, homelessness, context):
        step.run()
