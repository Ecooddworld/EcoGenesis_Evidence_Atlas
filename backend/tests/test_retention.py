from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import os
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "prune_runtime_artifacts.py"
SPEC = importlib.util.spec_from_file_location("prune_runtime_artifacts", SCRIPT_PATH)
assert SPEC and SPEC.loader
retention = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(retention)


def test_retention_plan_is_age_bounded_and_keeps_latest(tmp_path: Path) -> None:
    root = tmp_path / "barcode-runs"
    root.mkdir()
    timestamps = [1_700_000_000, 1_710_000_000, 1_720_000_000]
    for index, timestamp in enumerate(timestamps):
        directory = root / f"run-{index}"
        directory.mkdir()
        (directory / "artifact.json").write_text("{}", encoding="utf-8")
        os.utime(directory, (timestamp, timestamp))

    plan = retention.retention_plan(
        tmp_path,
        older_than_days=30,
        keep_latest=1,
        now=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )

    assert [item["run_id"] for item in plan] == ["run-1", "run-0"]
    assert (root / "run-0").exists()
    assert (root / "run-2").exists()
