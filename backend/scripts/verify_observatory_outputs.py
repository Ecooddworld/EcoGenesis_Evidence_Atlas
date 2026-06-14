from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys
import zipfile
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
REPORT_DIR = REPO_ROOT / "reports" / "observatory-demo"

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


def main() -> None:
    report = verify_observatory_outputs(REPORT_DIR)
    (REPORT_DIR / "observatory_output_verification.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (REPORT_DIR / "observatory_output_verification.md").write_text(verification_md(report), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    if report["summary"]["status"] != "pass":
        sys.exit(1)


def verify_observatory_outputs(report_dir: Path = REPORT_DIR) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    pack = load_json(report_dir / "observatory_evidence_pack.json")
    proof = load_json(report_dir / "proof_summary.json")
    manifest_rows = read_csv(report_dir / "observatory_demo_manifest.csv")
    manifest_by_name = {row["name"]: row for row in manifest_rows}
    pack_exports_by_name = {row["name"]: row for row in pack.get("exports", [])}
    artifact_checksums = pack.get("run", {}).get("artifact_checksums", {})
    zip_path = report_dir / "observatory_evidence_pack.zip"

    require(checks, "report_dir_exists", report_dir.is_dir(), str(report_dir))
    require(checks, "manifest_has_rows", len(manifest_rows) >= 40, f"{len(manifest_rows)} rows")
    for row in manifest_rows:
        path = report_dir / row["name"]
        actual_sha = sha256_file(path) if path.exists() else None
        require(checks, f"sha256:{row['name']}", actual_sha == row["sha256"], actual_sha or "missing")

    require(checks, "proof_total_20", proof.get("total") == 20, proof.get("total"))
    require(checks, "proof_hard_gate_pass", proof.get("hard_gate_failures") == 0, proof.get("hard_gate_failures"))
    require(checks, "all_opo_artifacts_present", REQUIRED_OPO_ARTIFACTS <= set(manifest_by_name), sorted(REQUIRED_OPO_ARTIFACTS - set(manifest_by_name)))
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

    require(checks, "vsea_parquet_magic", read_magic(report_dir / "observatory_vsea.parquet") == b"PAR1", read_magic(report_dir / "observatory_vsea.parquet"))
    require(checks, "occurrence_parquet_magic", read_magic(report_dir / "gbif_occurrence_context.parquet") == b"PAR1", read_magic(report_dir / "gbif_occurrence_context.parquet"))

    vsea_csv = read_csv(report_dir / "observatory_vsea.csv")
    occurrence_csv = read_csv(report_dir / "normalized_occurrence_context.csv")
    graph = load_json(report_dir / "observatory_graph.jsonld")
    require(checks, "vsea_count_matches_pack", len(vsea_csv) == len(pack.get("vsea", [])) == pack["summary"]["vsea_rows"], len(vsea_csv))
    require(
        checks,
        "occurrence_count_matches_pack",
        len(occurrence_csv) == len(pack.get("normalized_occurrence_context", [])) == pack["summary"]["normalized_occurrence_records"],
        len(occurrence_csv),
    )
    require(checks, "graph_items_have_provenance", all(item.get("provenance_hash") for item in graph.get("@graph", [])), len(graph.get("@graph", [])))
    require(checks, "graph_count_matches_summary", len(graph.get("@graph", [])) == pack["summary"]["graph_nodes"] + pack["summary"]["graph_edges"], len(graph.get("@graph", [])))

    visual_rows = read_csv(report_dir / "visualization_guardrail_audit.csv")
    ai_rows = read_csv(report_dir / "ai_dataset_export_audit.csv")
    gbif_rows = read_csv(report_dir / "gbif_export_claim_boundary_audit.csv")
    require(checks, "visualization_no_promotion", all(row.get("status") == "pass" for row in visual_rows), status_counts(visual_rows))
    require(checks, "ai_export_no_false_verified", all(row.get("status") == "pass" for row in ai_rows), status_counts(ai_rows))
    require(checks, "gbif_export_boundary_pass", all(row.get("status") == "pass" for row in gbif_rows), status_counts(gbif_rows))
    require(
        checks,
        "weak_rows_not_positive_verified",
        all(not (row.get("claim_state") == "weak_hypothesis" and row.get("ai_label") == "positive_verified") for row in pack.get("vsea", [])),
        "weak rows checked",
    )

    require(checks, "snapshot_hash_present", bool(pack.get("snapshot_manifest", {}).get("snapshot_hash")), pack.get("snapshot_manifest", {}).get("snapshot_id"))
    require(checks, "source_registry_audit_pass", load_json(report_dir / "source_registry_audit.json").get("status") == "pass", "source registry")

    with zipfile.ZipFile(zip_path) as archive:
        zip_names = set(archive.namelist())
    expected_in_zip = {row["name"] for row in manifest_rows if row["name"] != zip_path.name}
    require(checks, "zip_contains_report_artifacts", expected_in_zip <= zip_names, sorted(expected_in_zip - zip_names)[:8])

    failed = [check for check in checks if check["status"] != "pass"]
    return {
        "schema": "ecogenesis.gsig.observatory.output_verification.v1",
        "summary": {
            "status": "pass" if not failed else "fail",
            "checks": len(checks),
            "failed": len(failed),
            "report_dir": str(report_dir),
            "vsea_rows": len(vsea_csv),
            "occurrence_rows": len(occurrence_csv),
            "zip_entries": len(zip_names),
        },
        "checks": checks,
    }


def require(checks: list[dict[str, Any]], name: str, predicate: bool, observed: Any) -> None:
    checks.append(
        {
            "name": name,
            "status": "pass" if predicate else "fail",
            "observed": json_safe(observed),
        }
    )


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
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


def status_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = row.get("status", "missing")
        counts[status] = counts.get(status, 0) + 1
    return counts


def verification_md(report: dict[str, Any]) -> str:
    failed = [check for check in report["checks"] if check["status"] != "pass"]
    failed_lines = "\n".join(f"- `{check['name']}`: {check['observed']}" for check in failed) or "- none"
    return f"""# Observatory Output Verification

Status: `{report['summary']['status']}`

- Checks: `{report['summary']['checks']}`
- Failed: `{report['summary']['failed']}`
- VSEA rows: `{report['summary']['vsea_rows']}`
- Occurrence rows: `{report['summary']['occurrence_rows']}`
- ZIP entries: `{report['summary']['zip_entries']}`

## Failed Checks

{failed_lines}
"""


if __name__ == "__main__":
    main()
