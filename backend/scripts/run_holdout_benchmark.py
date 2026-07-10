from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.barcode.benchmark import benchmark_contract, run_holdout_benchmark
from app.barcode.scientific_gates import ATTESTATION_SECRET_ENV


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an independent EcoGenesis holdout benchmark.",
        epilog=(
            f"A release-eligible manifest is signed only when {ATTESTATION_SECRET_ENV} "
            "is configured with at least 32 bytes. The secret is intentionally not accepted as a CLI argument."
        ),
    )
    parser.add_argument("--dataset", help="JSON dataset satisfying the printed manifest contract")
    parser.add_argument("--output-dir", default="reports/independent-holdout-benchmark")
    parser.add_argument("--print-contract", action="store_true")
    args = parser.parse_args()
    if args.print_contract or not args.dataset:
        print(json.dumps({"status": "blocked", "release_eligible": False, "contract": benchmark_contract()}, indent=2))
        return
    summary = run_holdout_benchmark(dataset_path=Path(args.dataset), output_dir=Path(args.output_dir))
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    raise SystemExit(0 if summary["release_eligible"] else 2)


if __name__ == "__main__":
    main()
