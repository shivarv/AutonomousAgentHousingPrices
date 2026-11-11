"""Vercel serverless entrypoint for the FastAPI backend.

Deploy this as its own Vercel project with Root Directory = repository root. Vercel installs
only the runtime packages in /requirements.txt (the pipeline's heavy packages are not needed
to serve the API), and vercel.json rewrites every path here. The app's routes already start
with /api, so URLs are the same as in local development.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402

__all__ = ["app"]
