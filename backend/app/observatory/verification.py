from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any
import zipfile

from .storage import load_observatory_pack, observatory_artifact_path, observatory_export_manifest


REQUIRED_OPO_ARTIFACTS = {
    "source_registry_audit.json",
    "snapshot_manifest.json",
    "api_policy_audit.csv",
    "gbif_query_strategy_audit.csv",
    "source_provenance_manifest.json",
    "vsea_provenance_audit.csv",
    "visualization_guardrail_audit.csv",
    "blocked_claim_visibility_audit.csv",
    "sharedness_visual_overclaim_audit.csv",
    "ai_dataset_export_audit.csv",
    "literature_claim_state_audit.csv",
    "contradiction_visual_audit.csv",
    "gbif_export_claim_boundary_audit.csv",
    "repair_optimizer_guardrail_audit.csv",
    "offline_demo_reproducibility.json",
    "ui_ledger_consistency_audit.csv",
    "graph_roundtrip_audit.csv",
    "source_freshness_claim_audit.csv",
    "license_blocker_audit.csv",
    "judge_mode_non_claims_audit.csv",
}

SELF_REFERENTIAL_EXPORTS = {"observatory_evidence_pack.json", "observatory_evidence_pack.zip"}


def verify_observatory_run_outputs(run_id: str) -> dict[str, Any]:
    pack = load_observatory_pack(run_id)
    run_dir = observatory_artifact_path(run_id, "observatory_evidence_pack.json").parent
    checks: list[dict[str, Any]] = []
    manifest_rows = observatory_export_manifest(run_id)
    manifest_by_name = {row["name"]: row for row in manifest_rows}
    pack_exports_by_name = {row.get("name"): row for row in pack.get("exports", []) if row.get("name")}
    artifact_checksums = pack.get("run", {}).get("artifact_checksums", {})
    summary = pack.get("summary", {})

    require(checks, "run_dir_exists", run_dir.is_dir(), str(run_dir))
    require(checks, "manifest_has_competition_artifacts", len(manifest_rows) >= 40, f"{len(manifest_rows)} exports")
    for row in manifest_rows:
        path = observatory_artifact_path(run_id, row["name"])
        actual_sha = sha256_file(path) if path.exists() else None
        require(checks, f"sha256:{row['name']}", actual_sha == row.get("sha256"), actual_sha or "missing")

    proof = load_json_object(observatory_artifact_path(run_id, "proof_summary.json"))
    require(checks, "proof_total_20", proof.get("total") == 20, proof.get("total"))
    require(checks, "proof_hard_gate_pass", proof.get("hard_gate_failures") == 0, proof.get("hard_gate_failures"))
    require(
        checks,
        "proof_summary_matches_pack",
        proof.get("hard_gate_status") == pack.get("proof_summary", {}).get("hard_gate_status")
        and proof.get("total") == pack.get("proof_summary", {}).get("total"),
        {"artifact": proof.get("hard_gate_status"), "pack": pack.get("proof_summary", {}).get("hard_gate_status")},
    )
    require(
        checks,
        "all_opo_artifacts_present",
        REQUIRED_OPO_ARTIFACTS <= set(manifest_by_name),
        sorted(REQUIRED_OPO_ARTIFACTS - set(manifest_by_name)),
    )
    require(
        checks,
        "embedded_export_checksums_match_manifest",
        all(
            item.get("sha256") == manifest_by_name.get(name, {}).get("sha256")
            for name, item in pack_exports_by_name.items()
            if name not in SELF_REFERENTIAL_EXPORTS
        ),
        "non-self exports checked",
    )
    require(
        checks,
        "self_referential_exports_deferred",
        all(
            pack_exports_by_name.get(name, {}).get("sha256") in {None, ""}
            and pack_exports_by_name.get(name, {}).get("checksum_status") == "external_manifest_only"
            and manifest_by_name.get(name, {}).get("sha256")
            for name in SELF_REFERENTIAL_EXPORTS
        ),
        {name: pack_exports_by_name.get(name) for name in sorted(SELF_REFERENTIAL_EXPORTS)},
    )
    require(
        checks,
        "api_manifest_has_self_checksums",
        all(manifest_by_name.get(name, {}).get("sha256") for name in SELF_REFERENTIAL_EXPORTS),
        {name: manifest_by_name.get(name, {}).get("sha256") for name in sorted(SELF_REFERENTIAL_EXPORTS)},
    )
    require(
        checks,
        "artifact_checksums_exclude_self_references",
        not (SELF_REFERENTIAL_EXPORTS & set(artifact_checksums)),
        sorted(SELF_REFERENTIAL_EXPORTS & set(artifact_checksums)),
    )
    require(
        checks,
        "artifact_checksums_match_manifest",
        all(sha == manifest_by_name.get(name, {}).get("sha256") for name, sha in artifact_checksums.items()),
        f"{len(artifact_checksums)} embedded checksums",
    )

    require(
        checks,
        "vsea_parquet_magic",
        read_magic(observatory_artifact_path(run_id, "observatory_vsea.parquet")) == b"PAR1",
        read_magic(observatory_artifact_path(run_id, "observatory_vsea.parquet")),
    )
    require(
        checks,
        "occurrence_parquet_magic",
        read_magic(observatory_artifact_path(run_id, "gbif_occurrence_context.parquet")) == b"PAR1",
        read_magic(observatory_artifact_path(run_id, "gbif_occurrence_context.parquet")),
    )

    vsea_csv = read_csv_rows(observatory_artifact_path(run_id, "observatory_vsea.csv"))
    occurrence_csv = read_csv_rows(observatory_artifact_path(run_id, "normalized_occurrence_context.csv"))
    graph = load_json_object(observatory_artifact_path(run_id, "observatory_graph.jsonld"))
    graph_items = graph.get("@graph", []) if isinstance(graph.get("@graph"), list) else []
    require(
        checks,
        "vsea_count_matches_pack",
        len(vsea_csv) == len(pack.get("vsea", [])) == summary.get("vsea_rows"),
        {"csv": len(vsea_csv), "pack": len(pack.get("vsea", [])), "summary": summary.get("vsea_rows")},
    )
    require(
        checks,
        "occurrence_count_matches_pack",
        len(occurrence_csv)
        == len(pack.get("normalized_occurrence_context", []))
        == summary.get("normalized_occurrence_records"),
        {
            "csv": len(occurrence_csv),
            "pack": len(pack.get("normalized_occurrence_context", [])),
            "summary": summary.get("normalized_occurrence_records"),
        },
    )
    require(checks, "graph_items_have_provenance", all(item.get("provenance_hash") for item in graph_items), len(graph_items))
    require(
        checks,
        "graph_count_matches_summary",
        len(graph_items) == summary.get("graph_nodes", 0) + summary.get("graph_edges", 0),
        {"graph": len(graph_items), "summary_nodes_edges": summary.get("graph_nodes", 0) + summary.get("graph_edges", 0)},
    )

    visual_rows = read_csv_rows(observatory_artifact_path(run_id, "visualization_guardrail_audit.csv"))
    ai_rows = read_csv_rows(observatory_artifact_path(run_id, "ai_dataset_export_audit.csv"))
    gbif_rows = read_csv_rows(observatory_artifact_path(run_id, "gbif_export_claim_boundary_audit.csv"))
    require(checks, "visualization_no_promotion", bool(visual_rows) and all_pass(visual_rows), status_counts(visual_rows))
    require(checks, "ai_export_no_false_verified", bool(ai_rows) and all_pass(ai_rows), status_counts(ai_rows))
    require(checks, "gbif_export_boundary_pass", bool(gbif_rows) and all_pass(gbif_rows), status_counts(gbif_rows))
    require(
        checks,
        "weak_rows_not_positive_verified",
        all(
            not (row.get("claim_state") == "weak_hypothesis" and row.get("ai_label") == "positive_verified")
            for row in pack.get("vsea", [])
        ),
        "weak rows checked",
    )
    require(
        checks,
        "snapshot_hash_present",
        bool(pack.get("snapshot_manifest", {}).get("snapshot_hash")),
        pack.get("snapshot_manifest", {}).get("snapshot_id"),
    )
    require(
        checks,
        "source_registry_audit_pass",
        load_json_object(observatory_artifact_path(run_id, "source_registry_audit.json")).get("status") == "pass",
        "source registry",
    )
    require(
        checks,
        "contract_validation_pass",
        pack.get("run", {}).get("contract_validation", {}).get("status") == "pass",
        pack.get("run", {}).get("contract_validation", {}).get("status"),
    )
    require(
        checks,
        "summary_release_gate_pass",
        summary.get("hard_gate_status") == "pass" and summary.get("hard_gate_failures") == 0,
        {"status": summary.get("hard_gate_status"), "hard_gate_failures": summary.get("hard_gate_failures")},
    )
    require(checks, "claim_boundary_present", bool(summary.get("claim_boundary")), summary.get("claim_boundary"))

    zip_path = observatory_artifact_path(run_id, "observatory_evidence_pack.zip")
    zip_names: set[str] = set()
    zip_entry_sha_errors: list[dict[str, Any]] = []
    zip_error: str | None = None
    if zip_path.exists():
        try:
            with zipfile.ZipFile(zip_path) as archive:
                zip_names = set(archive.namelist())
                for name in sorted(set(manifest_by_name) - {zip_path.name}):
                    if name not in zip_names:
                        continue
                    actual = hashlib.sha256(archive.read(name)).hexdigest()
                    expected = manifest_by_name.get(name, {}).get("sha256")
                    if actual != expected:
                        zip_entry_sha_errors.append({"name": name, "actual": actual, "expected": expected})
        except zipfile.BadZipFile as exc:
            zip_error = str(exc)
    else:
        zip_error = "missing"
    require(checks, "zip_readable", zip_error is None, zip_error or zip_path.name)
    expected_in_zip = {row["name"] for row in manifest_rows if row["name"] != zip_path.name}
    require(checks, "zip_contains_run_artifacts", expected_in_zip <= zip_names, sorted(expected_in_zip - zip_names)[:8])
    require(
        checks,
        "zip_entry_checksums_match_manifest",
        not zip_entry_sha_errors,
        zip_entry_sha_errors[:8] or f"{len(zip_names)} entries checked",
    )

    failed = [check for check in checks if check["status"] != "pass"]
    return {
        "schema": "ecogenesis.gsig.observatory.run_output_verification.v1",
        "run_id": run_id,
        "summary": {
            "status": "pass" if not failed else "fail",
            "checks": len(checks),
            "failed": len(failed),
            "exports": len(manifest_rows),
            "vsea_rows": len(vsea_csv),
            "occurrence_rows": len(occurrence_csv),
            "zip_entries": len(zip_names),
        },
        "top_failures": failed[:8],
        "checks": checks,
    }


def verification_report_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    checks = report.get("checks", [])
    failed = [check for check in checks if check.get("status") != "pass"]
    core_check_names = [
        "proof_hard_gate_pass",
        "embedded_export_checksums_match_manifest",
        "self_referential_exports_deferred",
        "vsea_count_matches_pack",
        "occurrence_count_matches_pack",
        "graph_items_have_provenance",
        "visualization_no_promotion",
        "ai_export_no_false_verified",
        "gbif_export_boundary_pass",
        "zip_entry_checksums_match_manifest",
    ]
    checks_by_name = {check.get("name"): check for check in checks}
    core_rows = "\n".join(
        f"| `{name}` | `{checks_by_name.get(name, {}).get('status', 'missing')}` |"
        for name in core_check_names
    )
    failure_lines = "\n".join(
        f"- `{check.get('name')}`: `{check.get('observed')}`"
        for check in failed[:12]
    ) or "- none"
    return f"""# Observatory Run Output Verification

Run ID: `{report.get("run_id")}`

Status: `{summary.get("status")}`

| Metric | Value |
| --- | ---: |
| Checks | `{summary.get("checks", 0)}` |
| Failed | `{summary.get("failed", 0)}` |
| Exports checked | `{summary.get("exports", 0)}` |
| VSEA rows checked | `{summary.get("vsea_rows", 0)}` |
| Occurrence rows checked | `{summary.get("occurrence_rows", 0)}` |
| ZIP entries checked | `{summary.get("zip_entries", 0)}` |

## Core Gates

| Gate | Status |
| --- | --- |
{core_rows}

## Failed Checks

{failure_lines}

## Claim Boundary

This verification proves file integrity, row accounting, graph provenance, proof obligations, and export guardrails for this exact run. It does not upgrade GBIF occurrence context into molecular proof; claim strength remains controlled by the VSEA and graph gates.
"""


def require(checks: list[dict[str, Any]], name: str, predicate: bool, observed: Any) -> None:
    checks.append({"name": name, "status": "pass" if predicate else "fail", "observed": json_safe(observed)})


def load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_magic(path: Path) -> bytes:
    return path.read_bytes()[:4] if path.exists() else b""


def all_pass(rows: list[dict[str, str]]) -> bool:
    return all(row.get("status") == "pass" for row in rows)


def status_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = row.get("status", "missing")
        counts[status] = counts.get(status, 0) + 1
    return counts


def json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value
