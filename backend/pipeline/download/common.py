"""Shared download helpers.

Every download is idempotent: if the target file exists it is left untouched (data/raw is
read-only once downloaded). Each source folder gets a ``manifest.json`` recording, per file,
the URL, download timestamp, size and sha256 so DATA_SOURCES.md and the data_sources table can
be built from it.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from pipeline.paths import RAW_DIR

log = logging.getLogger("pipeline.download")

USER_AGENT = "ma-housing-need-research/0.1 (public-data pipeline)"
# Some public-data portals (e.g. huduser.gov) reject non-browser clients with an empty 202.
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
CHUNK = 1 << 20


def source_dir(source: str) -> Path:
    path = RAW_DIR / source
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def _manifest_path(folder: Path) -> Path:
    return folder / "manifest.json"


def read_manifest(folder: Path) -> dict[str, Any]:
    path = _manifest_path(folder)
    if path.exists():
        return json.loads(path.read_text())
    return {"files": {}}


def record(folder: Path, filename: str, url: str, extra: dict[str, Any] | None = None) -> None:
    """Add/refresh a manifest entry for a file that now exists in ``folder``."""
    manifest = read_manifest(folder)
    target = folder / filename
    entry = manifest["files"].get(filename, {})
    if entry.get("sha256") and entry.get("size") == target.stat().st_size:
        return
    manifest["files"][filename] = {
        "url": url,
        "downloaded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "size": target.stat().st_size,
        "sha256": _sha256(target),
        **(extra or {}),
    }
    _manifest_path(folder).write_text(json.dumps(manifest, indent=2, sort_keys=True))


def download(
    url: str,
    folder: Path,
    filename: str | None = None,
    *,
    params: dict[str, Any] | None = None,
    retries: int = 4,
    timeout: int = 120,
    min_bytes: int = 1,
    extra: dict[str, Any] | None = None,
    record_url: str | None = None,
    user_agent: str = USER_AGENT,
) -> Path:
    """Stream ``url`` into ``folder/filename`` unless it already exists. Returns the path."""
    filename = filename or url.rstrip("/").split("/")[-1].split("?")[0]
    target = folder / filename
    if target.exists() and target.stat().st_size >= min_bytes:
        log.info("exists, skipping: %s", target)
        record(folder, filename, record_url or url, extra)
        return target

    tmp = target.with_suffix(target.suffix + ".part")
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with requests.get(
                url,
                params=params,
                stream=True,
                timeout=timeout,
                headers={"User-Agent": user_agent},
            ) as resp:
                resp.raise_for_status()
                with tmp.open("wb") as fh:
                    for block in resp.iter_content(CHUNK):
                        fh.write(block)
            if tmp.stat().st_size < min_bytes:
                raise OSError(f"download too small ({tmp.stat().st_size} bytes): {url}")
            tmp.rename(target)
            log.info("downloaded %s (%d bytes)", target, target.stat().st_size)
            record(folder, filename, record_url or url, extra)
            return target
        except (requests.RequestException, OSError) as exc:
            last_error = exc
            log.warning("attempt %d/%d failed for %s: %s", attempt, retries, url, exc)
            time.sleep(2**attempt)
    if tmp.exists():
        tmp.unlink()
    raise RuntimeError(f"failed to download {url}") from last_error


def save_json(folder: Path, filename: str, payload: Any, url: str, **extra: Any) -> Path:
    """Write an API response (already fetched) as an untouched JSON file and record it."""
    target = folder / filename
    target.write_text(json.dumps(payload))
    record(folder, filename, url, extra or None)
    return target


def check_zip(path: Path) -> None:
    with zipfile.ZipFile(path) as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError(f"corrupt member {bad} in {path}")


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
