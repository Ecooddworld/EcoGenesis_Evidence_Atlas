from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evidence.pipeline import run_evidence_passport
from app.evidence.schemas import EvidenceRunRequest
from app.evidence.storage import artifact_path


def parse_bbox(value: str) -> list[float]:
    parts = [float(part.strip()) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("bbox must be west,south,east,north")
    west, south, east, north = parts
    if west >= east or south >= north:
        raise argparse.ArgumentTypeError("bbox must be ordered west,south,east,north")
    return parts


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a reproducible GBIF Evidence Passport.")
    parser.add_argument("--taxon", default="Aedes albopictus")
    parser.add_argument("--taxon-key", type=int, default=None)
    parser.add_argument("--region-name", default="Spain live GBIF bbox")
    parser.add_argument("--bbox", type=parse_bbox, default=parse_bbox("-10,35,4.5,44.5"))
    parser.add_argument(
        "--purpose",
        choices=["conservation_brief", "invasive_watch", "sampling_gaps", "dataset_quality_review"],
        default="invasive_watch",
    )
    parser.add_argument(
        "--source-mode",
        choices=["online", "online_with_empty_fallback", "online_with_fixture_fallback", "fixture"],
        default="online_with_empty_fallback",
    )
    parser.add_argument("--max-records", type=int, default=300)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/cli-run"))
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    os.environ.setdefault("EVIDENCE_DATA_DIR", str(repo_root / "data"))
    output_dir = args.output_dir if args.output_dir.is_absolute() else repo_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    request = EvidenceRunRequest(
        taxon=args.taxon,
        taxon_key=args.taxon_key,
        region_name=args.region_name,
        bbox=args.bbox,
        purpose=args.purpose,
        source_mode=args.source_mode,
        use_fixture=args.source_mode == "fixture",
        max_records=args.max_records,
    )
    pack = run_evidence_passport(request)
    for export in pack["exports"]:
        shutil.copy2(artifact_path(pack["run"]["run_id"], export["name"]), output_dir / export["name"])
    (output_dir / "request.json").write_text(json.dumps(request.model_dump(), indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "run_id": pack["run"]["run_id"],
                "output_dir": str(output_dir),
                "source_mode": pack["source_summary"]["used_source_mode"],
                "gbif_api_status": pack["source_summary"]["gbif_api_status"],
                "records_used": pack["passport"]["records_used"],
                "evidence_pack": str(output_dir / "evidence_pack.zip"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
