from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.barcode.compiler import run_barcode_compiler
from app.barcode.demo import (
    AMBIGUOUS_RECORD,
    DEFAULT_BARCODE_REQUEST,
    GOOD_RECORD,
    MISSING_METADATA_RECORD,
    WEAK_RECORD,
    base_metadata,
    request_with_records,
    sequence_record,
)
from app.barcode.math_audit import audit_pack_math
from app.barcode.schemas import BarcodeCompilerRequest


REPORT_DIR = REPO_ROOT / "reports" / "math-viability-audit"


def main() -> None:
    report = build_math_viability_report()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "math_viability_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (REPORT_DIR / "math_viability_report.md").write_text(report_markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    if report["summary"]["status"] != "pass":
        sys.exit(1)


def build_math_viability_report() -> dict[str, Any]:
    packs = [
        ("default_mixed_demo", run_barcode_compiler(BarcodeCompilerRequest(**DEFAULT_BARCODE_REQUEST))),
        ("edge_case_suite", run_barcode_compiler(BarcodeCompilerRequest(**edge_case_request()))),
    ]
    pack_reports = [audit_pack_math(pack, scope=name) for name, pack in packs]
    checks = [check for pack_report in pack_reports for check in pack_report["checks"]]
    failed = [check for check in checks if check["status"] != "pass"]
    return {
        "schema": "ecogenesis.math_viability_report.v1",
        "summary": {
            "status": "pass" if not failed else "fail",
            "packs": len(pack_reports),
            "checks": len(checks),
            "failed": len(failed),
        },
        "scope": [
            "Barcode compiler formulas and hard-gate invariants",
            "Taxonomic status versus publication/export status separation",
            "GSEG/GSIG claim-state viability as represented in generated evidence packs",
        ],
        "non_claim_boundaries": [
            "This is an internal consistency and fail-closed proof over supplied inputs.",
            "It is not an empirical species-delimitation validation over global biodiversity.",
            "It is not a claim that GBIF occurrence context upgrades molecular evidence.",
        ],
        "packs": pack_reports,
    }


def edge_case_request() -> dict[str, Any]:
    negative_gap = clone_record(GOOD_RECORD, "MATH-negative-gap")
    negative_gap["barcode_gap"] = {"intra_max_distance": 0.02, "inter_min_distance": 0.015}

    missing_diagnostic = clone_record(GOOD_RECORD, "MATH-missing-diagnostic")
    missing_diagnostic["diagnostic"] = {
        "diagnostic_kmers": [],
        "reference_total_windows": 5_000_000,
        "epsilon": 0.01,
    }

    q_pcr_missing_controls = clone_record(GOOD_RECORD, "MATH-qPCR-controls")
    q_pcr_missing_controls["metadata"]["assayType"] = "qpcr_ddpcr"

    no_match = sequence_record("MATH-no-match", [], metadata=base_metadata("MATH-no-match"))
    no_match["metadata"]["identity"] = 0
    no_match["metadata"]["queryCoverage"] = 0

    return request_with_records(
        "Math viability edge case suite",
        [
            clone_record(GOOD_RECORD, "MATH-good"),
            clone_record(AMBIGUOUS_RECORD, "MATH-ambiguous"),
            clone_record(WEAK_RECORD, "MATH-weak"),
            clone_record(MISSING_METADATA_RECORD, "MATH-metadata-gap"),
            negative_gap,
            missing_diagnostic,
            q_pcr_missing_controls,
            no_match,
        ],
    )


def clone_record(record: dict[str, Any], sequence_id: str) -> dict[str, Any]:
    out = deepcopy(record)
    out["sequence_id"] = sequence_id
    metadata = dict(out.get("metadata", {}))
    if metadata.get("occurrenceID"):
        metadata["occurrenceID"] = f"urn:ecogenesis:math:{sequence_id}"
    out["metadata"] = metadata
    return out


def report_markdown(report: dict[str, Any]) -> str:
    failed_lines = []
    for pack in report["packs"]:
        for check in pack["checks"]:
            if check["status"] != "pass":
                failed_lines.append(f"- `{pack['scope']}` / `{check['name']}`: `{check['observed']}`")
    failed_text = "\n".join(failed_lines) or "- none"
    pack_lines = "\n".join(
        f"- `{pack['scope']}`: `{pack['summary']['status']}`, "
        f"`{pack['summary']['checks']}` checks, `{pack['summary']['failed']}` failed"
        for pack in report["packs"]
    )
    boundaries = "\n".join(f"- {item}" for item in report["non_claim_boundaries"])
    return f"""# Math Viability Report

Status: `{report['summary']['status']}`

- Packs checked: `{report['summary']['packs']}`
- Checks: `{report['summary']['checks']}`
- Failed: `{report['summary']['failed']}`

## Packs

{pack_lines}

## Non-Claim Boundaries

{boundaries}

## Failed Checks

{failed_text}
"""


if __name__ == "__main__":
    main()
