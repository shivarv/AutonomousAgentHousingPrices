import json
from pathlib import Path

from pipeline.download import common


def test_download_skips_existing_file_and_records_manifest(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "file.csv"
    target.write_text("a,b\n1,2\n")

    def fail(*args, **kwargs):  # pragma: no cover - must not be called
        raise AssertionError("network must not be used when the file exists")

    monkeypatch.setattr(common.requests, "get", fail)
    path = common.download("https://example.org/file.csv", tmp_path)
    assert path == target
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    entry = manifest["files"]["file.csv"]
    assert entry["url"] == "https://example.org/file.csv"
    assert entry["size"] == target.stat().st_size
    assert len(entry["sha256"]) == 64
