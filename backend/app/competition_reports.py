from __future__ import annotations

import csv
from collections import Counter
import json
import os
from pathlib import Path
from typing import Any
import zipfile


REPORT_DEFINITIONS = {
    "competition-100-sequences": {
        "title": "Competition 100-sequence verification batch",
        "report": "competition_100_sequence_report.md",
        "results": "competition_100_sequence_results.csv",
        "manifest": "competition_100_sequence_manifest.csv",
        "exports": "competition_100_sequence_exports.json",
    },
    "adversarial-100-sequences": {
        "title": "Adversarial 100-sequence fail-closed stress batch",
        "report": "adversarial_100_sequence_report.md",
        "results": "adversarial_100_sequence_results.csv",
        "manifest": "adversarial_100_sequence_manifest.csv",
        "exports": "adversarial_100_sequence_exports.json",
    },
}

REQUIRED_GSEG_GSIG_EXPORTS = {
    "theorem_checklist.json",
    "verified_segment_evidence_array.csv",
    "verified_segment_evidence_array.jsonl",
    "verified_segment_evidence_array.parquet",
    "gseg_graph_schema.json",
    "gsig_graph_schema.yaml",
    "evidence_graph.jsonld",
    "graph_provenance_audit.csv",
    "graph_roundtrip_audit.json",
    "vsea_graph_reconciliation.csv",
    "sharedness_overclaim_audit.csv",
    "function_claim_boundary_audit.csv",
    "ai_output_guardrail_audit.csv",
    "ai_dataset_export_audit.csv",
    "ruleset_diff_report.json",
    "report_consistency_audit.csv",
    "judge_reproducibility_report.md",
}

PUBLIC_REPORT_FILES = {
    "adversarial_100_sequence_report.md",
    "competition_100_sequence_report.md",
    "adversarial_100_sequence_results.csv",
    "competition_100_sequence_results.csv",
    "adversarial_100_sequence_manifest.csv",
    "competition_100_sequence_manifest.csv",
    "expected_vs_actual.csv",
    "decision_summary.csv",
    "evidence_pack.zip",
    "evidence_pack.json",
    "molecular_evidence_report.html",
    "verified_segment_evidence_array.csv",
    "verified_segment_evidence_array.jsonl",
    "verified_segment_evidence_array.parquet",
    "theorem_checklist.json",
    "graph_roundtrip_audit.json",
    "graph_provenance_audit.csv",
    "report_consistency_audit.csv",
    "judge_reproducibility_report.md",
    "ai_output_guardrail_audit.csv",
    "ai_dataset_export_audit.csv",
    "hard_gate_audit.csv",
    "run.json",
}


def competition_reports_root() -> Path:
    configured = os.getenv("COMPETITION_REPORTS_DIR")
    if configured:
        return Path(configured).resolve()

    cwd_reports = Path("./reports").resolve()
    if cwd_reports.is_dir():
        return cwd_reports

    repo_reports = Path(__file__).resolve().parents[2] / "reports"
    if repo_reports.is_dir():
        return repo_reports.resolve()

    return cwd_reports


def list_competition_report_summaries() -> dict[str, Any]:
    reports = [competition_report_summary(report_id) for report_id in REPORT_DEFINITIONS]
    status = "pass" if all(report.get("summary", {}).get("status") == "pass" for report in reports) else "review"
    return {
        "schema": "ecogenesis.competition_reports.index.v1",
        "status": status,
        "reports": reports,
    }


def competition_report_summary(report_id: str) -> dict[str, Any]:
    definition = report_definition(report_id)
    directory = competition_reports_root() / report_id
    if not directory.is_dir():
        return missing_report_summary(report_id, definition)

    results_rows = read_csv_rows(directory / definition["results"])
    manifest_rows = read_csv_rows(directory / definition["manifest"])
    pass_count = sum(row.get("pass") in {"True", "true", "1", "yes"} for row in results_rows)
    fail_count = len(results_rows) - pass_count
    decision_counts = Counter(row.get("actualDecisionClass", "missing") for row in results_rows)
    expected_counts = Counter(row.get("expectedDecisionClass", "missing") for row in results_rows)
    export_names = {path.name for path in directory.iterdir() if path.is_file()}
    returned_exports = load_json_list(directory / definition["exports"])
    zip_entries = zip_entry_names(directory / "evidence_pack.zip")
    theorem = load_json_object(directory / "theorem_checklist.json")
    graph_roundtrip = load_json_object(directory / "graph_roundtrip_audit.json")
    parquet_magic = read_magic(directory / "verified_segment_evidence_array.parquet")
    required_present = REQUIRED_GSEG_GSIG_EXPORTS <= export_names
    zip_contains_required = REQUIRED_GSEG_GSIG_EXPORTS <= zip_entries
    report_file = directory / definition["report"]
    summary_status = "pass" if (
        len(results_rows) == 100
        and fail_count == 0
        and required_present
        and zip_contains_required
        and parquet_magic == b"PAR1"
        and theorem.get("summary", {}).get("release_gate") == "pass"
        and theorem.get("summary", {}).get("fail") == 0
        and graph_roundtrip.get("status") == "pass"
        and report_file.exists()
    ) else "review"

    return {
        "schema": "ecogenesis.competition_reports.summary.v1",
        "report_id": report_id,
        "title": definition["title"],
        "summary": {
            "status": summary_status,
            "records": len(results_rows),
            "expected_matched": pass_count,
            "expected_failed": fail_count,
            "exports": len(returned_exports) if returned_exports else len(export_names),
            "manifest_rows": len(manifest_rows),
            "zip_entries": len(zip_entries),
            "required_gseg_gsig_exports_present": required_present,
            "zip_contains_required_gseg_gsig_exports": zip_contains_required,
            "vsea_parquet_magic": parquet_magic.decode("utf-8", errors="replace") or "missing",
            "theorem_release_gate": theorem.get("summary", {}).get("release_gate", "missing"),
            "theorem_failures": theorem.get("summary", {}).get("fail"),
            "graph_roundtrip_status": graph_roundtrip.get("status", "missing"),
        },
        "decision_classes": dict(sorted(decision_counts.items())),
        "expected_classes": dict(sorted(expected_counts.items())),
        "downloads": competition_report_downloads(report_id, definition, export_names),
    }


def competition_report_path(report_id: str, file_name: str) -> Path:
    report_definition(report_id)
    clean_name = Path(file_name).name
    if clean_name != file_name or clean_name not in PUBLIC_REPORT_FILES:
        raise FileNotFoundError(file_name)
    path = competition_reports_root() / report_id / clean_name
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(file_name)
    return path


def report_definition(report_id: str) -> dict[str, str]:
    definition = REPORT_DEFINITIONS.get(report_id)
    if not definition:
        raise KeyError(report_id)
    return definition


def missing_report_summary(report_id: str, definition: dict[str, str]) -> dict[str, Any]:
    return {
        "schema": "ecogenesis.competition_reports.summary.v1",
        "report_id": report_id,
        "title": definition["title"],
        "summary": {
            "status": "missing",
            "records": 0,
            "expected_matched": 0,
            "expected_failed": 0,
            "exports": 0,
            "manifest_rows": 0,
            "zip_entries": 0,
            "required_gseg_gsig_exports_present": False,
            "zip_contains_required_gseg_gsig_exports": False,
            "vsea_parquet_magic": "missing",
            "theorem_release_gate": "missing",
            "theorem_failures": None,
            "graph_roundtrip_status": "missing",
        },
        "decision_classes": {},
        "expected_classes": {},
        "downloads": [],
    }


def competition_report_downloads(report_id: str, definition: dict[str, str], export_names: set[str]) -> list[dict[str, Any]]:
    priority = [
        definition["report"],
        definition["results"],
        definition["manifest"],
        "evidence_pack.zip",
        "molecular_evidence_report.html",
        "verified_segment_evidence_array.parquet",
        "theorem_checklist.json",
        "graph_roundtrip_audit.json",
        "judge_reproducibility_report.md",
    ]
    downloads = []
    for name in priority:
        if name in export_names:
            downloads.append(
                {
                    "name": name,
                    "url": f"/api/competition-reports/{report_id}/files/{name}",
                    "size_bytes": (competition_reports_root() / report_id / name).stat().st_size,
                }
            )
    return downloads


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def load_json_list(path: Path) -> list[Any]:
    if not path.exists():
        return []
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return loaded if isinstance(loaded, list) else []


def read_magic(path: Path) -> bytes:
    return path.read_bytes()[:4] if path.exists() else b""


def zip_entry_names(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        with zipfile.ZipFile(path) as archive:
            return {Path(name).name for name in archive.namelist()}
    except zipfile.BadZipFile:
        return set()
