from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


EXPECTED_CLASSES = {
    "AALB-COI-good": "species-safe",
    "AALB-COI-ambiguous": "genus-safe",
    "AALB-COI-short": "weak",
    "AALB-COI-metadata-gap": "not-publishable",
}

REQUIRED_EXPORTS = {
    "sequence_safety_table.csv",
    "safe_taxonomic_assignments.csv",
    "ambiguous_sequences.csv",
    "barcode_gap_report.csv",
    "diagnostic_kmer_report.csv",
    "gbif_backbone_matches.csv",
    "publication_blockers.csv",
    "dwc_occurrence_core_template.csv",
    "dna_derived_extension_template.csv",
    "molecular_evidence_report.html",
    "methods_text.md",
    "citations.md",
    "evidence_graph.json",
    "evidence_pack.json",
    "evidence_pack.zip",
}
REQUIRED_ZIP_MEMBERS = REQUIRED_EXPORTS - {"evidence_pack.zip"}


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    output_dir = repo_root / "reports" / "barcode-operability"
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="barcode-operability-") as temp_dir:
        os.environ["EVIDENCE_DATA_DIR"] = temp_dir

        from fastapi.testclient import TestClient

        from app.barcode.compiler import run_barcode_compiler
        from app.barcode.demo import DEFAULT_BARCODE_REQUEST
        from app.barcode.schemas import BarcodeCompilerRequest
        from app.barcode.storage import barcode_artifact_path
        from app.main import app

        direct_pack = run_barcode_compiler(BarcodeCompilerRequest(**DEFAULT_BARCODE_REQUEST))
        direct_checks = check_pack(direct_pack, barcode_artifact_path)

        client = TestClient(app)
        api_created = client.post("/api/barcode/run", json=DEFAULT_BARCODE_REQUEST)
        api_created.raise_for_status()
        run_id = api_created.json()["run_id"]
        api_detail = client.get(f"/api/barcode/runs/{run_id}")
        api_detail.raise_for_status()
        api_pack = api_detail.json()
        api_report = client.get(f"/api/barcode/runs/{run_id}/report")
        api_exports = client.get(f"/api/barcode/runs/{run_id}/exports")
        api_zip_head = client.head(f"/api/barcode/runs/{run_id}/exports/evidence_pack.zip")

        api_checks = {
            "run_endpoint_status": api_created.status_code,
            "detail_endpoint_status": api_detail.status_code,
            "report_endpoint_status": api_report.status_code,
            "exports_endpoint_status": api_exports.status_code,
            "zip_head_status": api_zip_head.status_code,
            "report_contains_title": "Barcode-to-GBIF Evidence Compiler" in api_report.text,
            "api_classes": classes_by_sequence(api_pack),
            "api_expected_classes_pass": classes_by_sequence(api_pack) == EXPECTED_CLASSES,
            "api_export_count": len(api_exports.json()),
        }

        report = {
            "status": "pass" if direct_checks["pass"] and api_checks["api_expected_classes_pass"] else "fail",
            "summary": {
                "tool": "Barcode-to-GBIF Evidence Compiler",
                "demo": "mixed batch",
                "meaning": "One run intentionally reaches species-safe, genus-safe, weak and not-publishable decisions.",
            },
            "expected_classes": EXPECTED_CLASSES,
            "direct_compiler": direct_checks,
            "api": api_checks,
            "actual_results": actual_results(direct_pack),
        }

    (output_dir / "operability_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "operability_report.md").write_text(markdown_report(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "report_dir": str(output_dir)}, indent=2))
    if report["status"] != "pass":
        raise SystemExit(1)


def check_pack(pack: dict, artifact_path_fn) -> dict:
    export_names = {item["name"] for item in pack["exports"]}
    missing_exports = sorted(REQUIRED_EXPORTS - export_names)
    actual_classes = classes_by_sequence(pack)
    zip_path = artifact_path_fn(pack["run"]["run_id"], "evidence_pack.zip")
    zip_names: set[str] = set()
    zip_ok = False
    if zip_path.exists():
        with zipfile.ZipFile(zip_path) as archive:
            zip_names = set(archive.namelist())
            bad_files = archive.testzip()
            zip_ok = bad_files is None
    evidence_json_path = artifact_path_fn(pack["run"]["run_id"], "evidence_pack.json")
    sha256 = hashlib.sha256(evidence_json_path.read_bytes()).hexdigest() if evidence_json_path.exists() else None
    return {
        "pass": not missing_exports and actual_classes == EXPECTED_CLASSES and zip_ok and REQUIRED_ZIP_MEMBERS <= zip_names,
        "run_id": pack["run"]["run_id"],
        "metrics": pack["metrics"],
        "actual_classes": actual_classes,
        "expected_classes_pass": actual_classes == EXPECTED_CLASSES,
        "missing_exports": missing_exports,
        "zip_ok": zip_ok,
        "zip_contains_required_exports": REQUIRED_ZIP_MEMBERS <= zip_names,
        "evidence_pack_json_sha256": sha256,
    }


def classes_by_sequence(pack: dict) -> dict[str, str]:
    return {record["sequence_id"]: record["decision_class"] for record in pack["records"]}


def actual_results(pack: dict) -> list[dict]:
    rows = []
    for record in pack["records"]:
        top = record["top_hit"] or {}
        rows.append(
            {
                "sequence_id": record["sequence_id"],
                "decision_class": record["decision_class"],
                "taxonomic_status": record["taxonomic_status"],
                "publication_status": record["publication_status"],
                "safe_taxon": record["safe_taxon"],
                "top_identity": top.get("identity"),
                "top_query_coverage": top.get("query_coverage"),
                "barcode_gap_status": record["barcode_gap"]["status"],
                "diagnostic_kmer_status": record["diagnostic_kmers"]["status"],
                "blockers": record["blockers"],
            }
        )
    return rows


def markdown_report(report: dict) -> str:
    lines = [
        "# Barcode Compiler Operability Report",
        "",
        f"Status: **{report['status'].upper()}**",
        "",
        "## Real Results",
        "",
        "| Sequence | Decision | Taxonomic status | Publication status | Safe taxon | Main blockers |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in report["actual_results"]:
        blockers = "; ".join(row["blockers"][:2]) if row["blockers"] else "none"
        lines.append(
            "| {sequence_id} | {decision_class} | {taxonomic_status} | {publication_status} | {safe_taxon} | {blockers} |".format(
                sequence_id=row["sequence_id"],
                decision_class=row["decision_class"],
                taxonomic_status=row["taxonomic_status"],
                publication_status=row["publication_status"],
                safe_taxon=f"{row['safe_taxon']['name']} ({row['safe_taxon']['rank']})",
                blockers=blockers,
            )
        )
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            "```json",
            json.dumps(report["direct_compiler"]["metrics"], indent=2, ensure_ascii=False),
            "```",
            "",
            "## Checks",
            "",
            f"- Direct compiler expected classes: `{report['direct_compiler']['expected_classes_pass']}`",
            f"- API expected classes: `{report['api']['api_expected_classes_pass']}`",
            f"- ZIP valid: `{report['direct_compiler']['zip_ok']}`",
            f"- Required exports present: `{not report['direct_compiler']['missing_exports']}`",
            f"- HTML report endpoint: `{report['api']['report_endpoint_status']}`",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
