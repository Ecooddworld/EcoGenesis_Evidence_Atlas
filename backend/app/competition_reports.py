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
        "title": "Competition 100-row repeated-fixture regression batch",
        "report": "competition_100_sequence_report.md",
        "results": "competition_100_sequence_results.csv",
        "manifest": "competition_100_sequence_manifest.csv",
        "exports": "competition_100_sequence_exports.json",
    },
    "adversarial-100-sequences": {
        "title": "Adversarial 100-row repeated-fixture regression batch",
        "report": "adversarial_100_sequence_report.md",
        "results": "adversarial_100_sequence_results.csv",
        "manifest": "adversarial_100_sequence_manifest.csv",
        "exports": "adversarial_100_sequence_exports.json",
    },
}

REQUIRED_GSEG_GSIG_EXPORTS = {
    "dwca_validation_report.json",
    "dwca_roundtrip_contract.json",
    "dwc_occurrence_core_validation_candidates.csv",
    "dna_derived_extension_validation_candidates.csv",
    "release_invariant_checklist.json",
    "math_viability_audit.json",
    "rule_evidence_segment_array.csv",
    "rule_evidence_segment_array.jsonl",
    "rule_evidence_segment_array.parquet",
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

RETIRED_PUBLIC_ALIASES = {
    "dwc_occurrence_core_gbif_ready.csv",
    "dna_derived_extension_gbif_ready.csv",
    "theorem_checklist.json",
    "verified_segment_evidence_array.csv",
    "verified_segment_evidence_array.jsonl",
    "verified_segment_evidence_array.parquet",
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
    "dwca_validation_report.json",
    "dwca_roundtrip_contract.json",
    "dwc_occurrence_core_validation_candidates.csv",
    "dna_derived_extension_validation_candidates.csv",
    "molecular_evidence_report.html",
    "rule_evidence_segment_array.csv",
    "rule_evidence_segment_array.jsonl",
    "rule_evidence_segment_array.parquet",
    "release_invariant_checklist.json",
    "math_viability_audit.json",
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
    scientific_state_counts = Counter(
        row.get("scientificDecisionState") or row.get("actualDecisionClass", "missing")
        for row in results_rows
    )
    expected_counts = Counter(row.get("expectedDecisionClass", "missing") for row in results_rows)
    export_names = {path.name for path in directory.iterdir() if path.is_file()}
    returned_exports = load_json_list(directory / definition["exports"])
    zip_entries = zip_entry_names(directory / "evidence_pack.zip")
    invariant = load_json_object(directory / "release_invariant_checklist.json")
    math_viability = load_json_object(directory / "math_viability_audit.json")
    graph_roundtrip = load_json_object(directory / "graph_roundtrip_audit.json")
    dwca_validation = load_json_object(directory / "dwca_validation_report.json")
    parquet_magic = read_magic(directory / "rule_evidence_segment_array.parquet")
    required_present = REQUIRED_GSEG_GSIG_EXPORTS <= export_names
    zip_contains_required = REQUIRED_GSEG_GSIG_EXPORTS <= zip_entries
    report_file = directory / definition["report"]
    regression_status = "pass" if (
        len(results_rows) == 100
        and fail_count == 0
        and required_present
        and zip_contains_required
        and parquet_magic == b"PAR1"
        and invariant.get("summary", {}).get("release_gate") in {"pass", "review"}
        and invariant.get("summary", {}).get("fail") == 0
        and math_viability.get("summary", {}).get("status") == "pass"
        and math_viability.get("summary", {}).get("failed") == 0
        and graph_roundtrip.get("status") == "pass"
        and report_file.exists()
    ) else "fail"
    summary_status = "review" if regression_status == "pass" else "fail"

    return {
        "schema": "ecogenesis.competition_reports.summary.v1",
        "report_id": report_id,
        "title": definition["title"],
        "summary": {
            "status": summary_status,
            "regression_status": regression_status,
            "validation_status": "external_validation_missing",
            "validation_boundary": (
                "The 100 rows are repeated regression fixtures, not 100 independent specimens or an empirical benchmark."
            ),
            "records": len(results_rows),
            "expected_matched": pass_count,
            "expected_failed": fail_count,
            "exports": len(returned_exports) if returned_exports else len(export_names),
            "manifest_rows": len(manifest_rows),
            "zip_entries": len(zip_entries),
            "required_gseg_gsig_exports_present": required_present,
            "zip_contains_required_gseg_gsig_exports": zip_contains_required,
            "retired_aliases_publicly_available": False,
            "rule_evidence_parquet_magic": parquet_magic.decode("utf-8", errors="replace") or "missing",
            "release_invariant_gate": invariant.get("summary", {}).get("release_gate", "missing"),
            "release_invariant_failures": invariant.get("summary", {}).get("fail"),
            "math_viability_status": math_viability.get("summary", {}).get("status", "missing"),
            "math_viability_failures": math_viability.get("summary", {}).get("failed"),
            "math_viability_checks": math_viability.get("summary", {}).get("checks"),
            "graph_roundtrip_status": graph_roundtrip.get("status", "missing"),
            "dwca_local_validation_status": dwca_validation.get("local_validation_status", "missing"),
            "dwca_release_gate": dwca_validation.get("release_gate", "missing"),
        },
        "decision_classes": dict(sorted(decision_counts.items())),
        "scientific_states": dict(sorted(scientific_state_counts.items())),
        "expected_classes": dict(sorted(expected_counts.items())),
        "downloads": competition_report_downloads(report_id, definition, export_names),
    }


def competition_report_path(report_id: str, file_name: str) -> Path:
    report_definition(report_id)
    clean_name = Path(file_name).name
    if (
        clean_name != file_name
        or clean_name in RETIRED_PUBLIC_ALIASES
        or clean_name not in PUBLIC_REPORT_FILES
    ):
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
            "retired_aliases_publicly_available": False,
            "regression_status": "missing",
            "validation_status": "external_validation_missing",
            "rule_evidence_parquet_magic": "missing",
            "release_invariant_gate": "missing",
            "release_invariant_failures": None,
            "math_viability_status": "missing",
            "math_viability_failures": None,
            "math_viability_checks": None,
            "graph_roundtrip_status": "missing",
            "dwca_local_validation_status": "missing",
            "dwca_release_gate": "missing",
        },
        "decision_classes": {},
        "scientific_states": {},
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
        "rule_evidence_segment_array.parquet",
        "release_invariant_checklist.json",
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
