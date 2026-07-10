#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil


RUNTIME_ROOTS = ("runs", "barcode-runs", "observatory-runs")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or apply age-based retention to runtime artifacts. Dry-run is the default.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(os.getenv("EVIDENCE_DATA_DIR", "./data")),
        help="Runtime data root (default: EVIDENCE_DATA_DIR or ./data).",
    )
    parser.add_argument("--older-than-days", type=int, default=30, help="Delete eligible directories older than this age.")
    parser.add_argument("--keep-latest", type=int, default=20, help="Always keep this many newest runs per runtime root.")
    parser.add_argument("--apply", action="store_true", help="Actually delete eligible directories.")
    return parser.parse_args()


def retention_plan(
    data_dir: Path,
    *,
    older_than_days: int,
    keep_latest: int,
    now: datetime | None = None,
) -> list[dict[str, object]]:
    if older_than_days < 1:
        raise ValueError("older_than_days must be at least 1")
    if keep_latest < 0:
        raise ValueError("keep_latest cannot be negative")
    current = now or datetime.now(timezone.utc)
    cutoff = current - timedelta(days=older_than_days)
    plan: list[dict[str, object]] = []
    resolved_data_dir = data_dir.resolve()
    for root_name in RUNTIME_ROOTS:
        root = (resolved_data_dir / root_name).resolve()
        if not root.exists():
            continue
        directories = sorted(
            (entry for entry in root.iterdir() if entry.is_dir() and not entry.is_symlink()),
            key=lambda entry: entry.stat().st_mtime,
            reverse=True,
        )
        protected = {entry.resolve() for entry in directories[:keep_latest]}
        for entry in directories:
            resolved_entry = entry.resolve()
            if root not in resolved_entry.parents:
                continue
            modified_at = datetime.fromtimestamp(entry.stat().st_mtime, timezone.utc)
            if resolved_entry in protected or modified_at >= cutoff:
                continue
            plan.append(
                {
                    "root": root_name,
                    "run_id": entry.name,
                    "path": str(resolved_entry),
                    "modified_at": modified_at.isoformat(),
                    "size_bytes": directory_size(entry),
                }
            )
    return plan


def directory_size(directory: Path) -> int:
    return sum(path.stat().st_size for path in directory.rglob("*") if path.is_file() and not path.is_symlink())


def apply_plan(plan: list[dict[str, object]]) -> None:
    for item in plan:
        shutil.rmtree(Path(str(item["path"])))


def main() -> None:
    args = parse_args()
    try:
        plan = retention_plan(
            args.data_dir,
            older_than_days=args.older_than_days,
            keep_latest=args.keep_latest,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.apply:
        apply_plan(plan)
    print(
        json.dumps(
            {
                "mode": "apply" if args.apply else "dry-run",
                "data_dir": str(args.data_dir.resolve()),
                "older_than_days": args.older_than_days,
                "keep_latest": args.keep_latest,
                "directories": len(plan),
                "bytes": sum(int(item["size_bytes"]) for item in plan),
                "items": plan,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
