from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.barcode.compiler import run_barcode_compiler
from app.barcode.demo import BARCODE_DEMO_SCENARIOS, DEFAULT_BARCODE_REQUEST
from app.barcode.schemas import BarcodeCompilerRequest
from app.barcode.storage import barcode_artifact_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Barcode-to-GBIF Evidence Compiler demo.")
    parser.add_argument("--demo-id", default="mixed-batch", help="Demo scenario id from /api/barcode/demo-scenarios.")
    parser.add_argument("--input-json", type=Path, help="Optional request JSON file.")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/barcode-demo"), help="Directory for copied artifacts.")
    return parser.parse_args()


def load_request(args: argparse.Namespace) -> dict:
    if args.input_json:
        return json.loads(args.input_json.read_text(encoding="utf-8"))
    for scenario in BARCODE_DEMO_SCENARIOS:
        if scenario["id"] == args.demo_id:
            return scenario["request"]
    return DEFAULT_BARCODE_REQUEST


def main() -> None:
    args = parse_args()
    request = BarcodeCompilerRequest(**load_request(args))
    pack = run_barcode_compiler(request)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for export in pack["exports"]:
        source = barcode_artifact_path(pack["run"]["run_id"], export["name"])
        shutil.copy2(source, args.output_dir / export["name"])
    (args.output_dir / "README.md").write_text(
        "\n".join(
            [
                "# Barcode Demo Evidence Pack",
                "",
                f"Run ID: `{pack['run']['run_id']}`",
                f"Project: {pack['summary']['project_title']}",
                f"Verdict: {pack['summary']['verdict']}",
                "",
                "Open `molecular_evidence_report.html` or inspect `sequence_safety_table.csv`.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"run_id": pack["run"]["run_id"], "output_dir": str(args.output_dir)}, indent=2))


if __name__ == "__main__":
    main()
