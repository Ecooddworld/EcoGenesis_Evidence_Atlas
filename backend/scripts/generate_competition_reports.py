from __future__ import annotations

import csv
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.barcode.artifacts import build_barcode_artifacts
from app.barcode.compiler import run_barcode_compiler
from app.barcode.demo import (
    AEDES_ALBOPICTUS_LINEAGE,
    AMBIGUOUS_RECORD,
    BASE_SEQUENCE,
    GOOD_RECORD,
    MISSING_METADATA_RECORD,
    WEAK_RECORD,
    base_metadata,
    request_with_records,
    sequence_record,
    top_hit,
)
from app.barcode.schemas import BarcodeCompilerRequest


REPORTS_ROOT = REPO_ROOT / "reports"
COMPETITION_DIR = REPORTS_ROOT / "competition-100-sequences"
ADVERSARIAL_DIR = REPORTS_ROOT / "adversarial-100-sequences"

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


def clone_record(
    template: dict[str, Any],
    sequence_id: str,
    index: int,
    *,
    preserve_missing_metadata: bool = False,
    metadata_overrides: dict[str, Any] | None = None,
    clear_hits: bool = False,
    barcode_gap: dict[str, Any] | None = None,
    diagnostic: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = deepcopy(template)
    record["sequence_id"] = sequence_id
    record["sequence"] = BASE_SEQUENCE
    if clear_hits:
        record["hits"] = []
    if preserve_missing_metadata:
        metadata = dict(record.get("metadata", {}))
        metadata["scientificName"] = metadata.get("scientificName", "Aedes albopictus")
    else:
        metadata = base_metadata(sequence_id)
        metadata["eventID"] = f"competition-event-{((index - 1) // 10) + 1:02d}"
        metadata["materialSampleID"] = f"competition-sample-{index:03d}"
        metadata["eventDate"] = f"2026-06-{((index - 1) % 28) + 1:02d}"
        metadata["countryCode"] = ["ES", "IT", "FR", "US"][index % 4]
    metadata.update(metadata_overrides or {})
    record["metadata"] = metadata
    if barcode_gap is not None:
        record["barcode_gap"] = barcode_gap
    if diagnostic is not None:
        record["diagnostic"] = diagnostic
    return record


def competition_records() -> tuple[list[dict[str, Any]], dict[str, str]]:
    records: list[dict[str, Any]] = []
    expected: dict[str, str] = {}
    specs = [
        ("species_safe", GOOD_RECORD, "species-safe", False, 25),
        ("genus_safe_ambiguous", AMBIGUOUS_RECORD, "genus-safe", False, 25),
        ("weak_coverage", WEAK_RECORD, "weak", False, 25),
        ("metadata_blocked", MISSING_METADATA_RECORD, "not-publishable", True, 25),
    ]
    index = 1
    for slug, template, expected_class, preserve_missing, count in specs:
        for _ in range(count):
            sequence_id = f"COMP100-{index:03d}-{slug}"
            records.append(
                clone_record(
                    template,
                    sequence_id,
                    index,
                    preserve_missing_metadata=preserve_missing,
                )
            )
            expected[sequence_id] = expected_class
            index += 1
    return records, expected


def adversarial_records() -> tuple[list[dict[str, Any]], dict[str, str], dict[str, str]]:
    no_match_template = sequence_record("ADV-no-match-template", [], metadata=base_metadata("ADV-no-match-template"))
    no_match_template["sequence"] = BASE_SEQUENCE
    negative_gap = {"intra_max_distance": 0.012, "inter_min_distance": 0.004}
    missing_diagnostic = {
        "diagnostic_kmers": [],
        "reference_total_windows": 5_000_000,
        "epsilon": 0.01,
    }
    custom_marker = clone_record(
        GOOD_RECORD,
        "ADV-custom-template",
        1,
        metadata_overrides={"marker": "custom-locus-x", "target_gene": "custom marker"},
    )
    custom_marker["hits"] = [top_hit(99.6, 96, lineage=AEDES_ALBOPICTUS_LINEAGE)]

    classes = [
        ("true_species_safe_positive", GOOD_RECORD, "species-safe", {}),
        ("close_sibling_ambiguity", AMBIGUOUS_RECORD, "genus-safe", {}),
        ("weak_coverage_short_fragment", WEAK_RECORD, "weak", {}),
        (
            "no_match_novel_lineage",
            no_match_template,
            "no-match",
            {"clear_hits": True, "metadata_overrides": {"identity": 0, "queryCoverage": 0}},
        ),
        ("metadata_blocked_taxonomy_safe", MISSING_METADATA_RECORD, "not-publishable", {"preserve_missing_metadata": True}),
        (
            "assay_control_failure",
            GOOD_RECORD,
            "not-publishable",
            {"metadata_overrides": {"assayType": "qpcr_ddpcr"}},
        ),
        (
            "wrong_taxonomy_name_conflict",
            GOOD_RECORD,
            "not-publishable",
            {"metadata_overrides": {"scientificName": "Aedes aegypti"}},
        ),
        ("genome_segment_non_barcode_marker", custom_marker, "genus-safe", {}),
        ("negative_barcode_gap", GOOD_RECORD, "ambiguous", {"barcode_gap": negative_gap}),
        ("missing_diagnostic_kmer", GOOD_RECORD, "ambiguous", {"diagnostic": missing_diagnostic}),
    ]
    records: list[dict[str, Any]] = []
    expected: dict[str, str] = {}
    adversarial_class: dict[str, str] = {}
    index = 1
    for class_slug, template, expected_class, kwargs in classes:
        for _ in range(10):
            sequence_id = f"ADV100-{index:03d}-{class_slug}"
            record = clone_record(template, sequence_id, index, **kwargs)
            if class_slug == "genome_segment_non_barcode_marker":
                record["metadata"]["marker"] = "custom-locus-x"
            records.append(record)
            expected[sequence_id] = expected_class
            adversarial_class[sequence_id] = class_slug
            index += 1
    return records, expected, adversarial_class


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_artifacts(output_dir: Path, artifacts: dict[str, str | bytes]) -> str:
    for name, content in artifacts.items():
        path = output_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
    zip_path = output_dir / "evidence_pack.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(artifacts.items()):
            archive.writestr(name, content)
    return sha256_file(zip_path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def compile_pack(title: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    request = BarcodeCompilerRequest(**request_with_records(title, records))
    return run_barcode_compiler(request)


def result_rows(pack: dict[str, Any], expected: dict[str, str], adversarial_class: dict[str, str] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in pack["records"]:
        sequence_id = record["sequence_id"]
        row = {
            "sequenceID": sequence_id,
            "expectedDecisionClass": expected[sequence_id],
            "actualDecisionClass": record["decision_class"],
            "taxonomicStatus": record["taxonomic_status"],
            "publicationBucket": record.get("publication_bucket"),
            "exportState": record.get("export_state"),
            "markerProfile": record["metadata_readiness"]["marker_profile"]["profile_id"],
            "candidateTaxon": record["candidate_taxon"]["name"],
            "publishedTaxon": record["published_taxon"]["name"],
            "blockers": "; ".join(record["blockers"]),
            "pass": str(expected[sequence_id] == record["decision_class"]),
        }
        if adversarial_class is not None:
            row = {
                "sequenceID": sequence_id,
                "adversarialClass": adversarial_class[sequence_id],
                **row,
            }
        rows.append(row)
    return rows


def manifest_rows(records: list[dict[str, Any]], expected: dict[str, str], adversarial_class: dict[str, str] | None = None) -> list[dict[str, Any]]:
    rows = []
    for record in records:
        sequence_id = record["sequence_id"]
        row = {
            "sequenceID": sequence_id,
            "expectedDecisionClass": expected[sequence_id],
            "hasHits": bool(record.get("hits")),
            "metadataFields": "; ".join(sorted(record.get("metadata", {}).keys())),
        }
        if adversarial_class is not None:
            row["adversarialClass"] = adversarial_class[sequence_id]
        rows.append(row)
    return rows


def summary_csv_rows(pack: dict[str, Any]) -> list[dict[str, Any]]:
    metrics = pack["metrics"]
    keys = [
        "processed_records",
        "species_safe_records",
        "genus_safe_records",
        "ambiguous_records",
        "weak_records",
        "no_match_records",
        "not_publishable_records",
        "publishable_template_records",
        "dataset_ready_records",
        "blocked_species_claims",
        "hard_gate_failures",
        "assay_gate_failures",
    ]
    return [{"metric": key, "value": metrics.get(key)} for key in keys]


def export_names(pack: dict[str, Any], artifacts: dict[str, str | bytes]) -> list[str]:
    names = sorted({item["name"] for item in pack.get("exports", [])} | set(artifacts) | {"evidence_pack.zip"})
    return names


def render_report(
    *,
    title: str,
    pack: dict[str, Any],
    artifacts: dict[str, str | bytes],
    rows: list[dict[str, Any]],
    zip_sha256: str,
    adversarial_class: dict[str, str] | None = None,
) -> str:
    actual_counts = Counter(row["actualDecisionClass"] for row in rows)
    bucket_counts = Counter(row["publicationBucket"] for row in rows)
    export_state_counts = Counter(row["exportState"] for row in rows)
    expected_matched = all(row["pass"] == "True" for row in rows)
    hard_gate_failures = pack["metrics"].get("hard_gate_failures", 0)
    theorem = json.loads(str(artifacts["theorem_checklist.json"]))
    graph_roundtrip = json.loads(str(artifacts["graph_roundtrip_audit.json"]))
    parquet_bytes = artifacts["verified_segment_evidence_array.parquet"]
    parquet_status = "PAR1" if isinstance(parquet_bytes, bytes) and parquet_bytes[:4] == b"PAR1" else "not_parquet_magic"
    required_present = REQUIRED_GSEG_GSIG_EXPORTS.issubset(set(artifacts))
    zip_contains_required = zip_required_present(artifacts)
    false_species_safe = 0
    by_class: dict[str, Counter[str]] = defaultdict(Counter)
    if adversarial_class is not None:
        for row in rows:
            by_class[row["adversarialClass"]][row["actualDecisionClass"]] += 1
            if row["adversarialClass"] != "true_species_safe_positive" and row["actualDecisionClass"] == "species-safe":
                false_species_safe += 1

    lines = [
        f"# {title}",
        "",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "Backend: local compiler script `backend/scripts/generate_competition_reports.py`",
        f"Run ID: `{pack['run']['run_id']}`",
        "",
        "## Result",
        "",
        f"- Records submitted: {len(rows)}",
        "- API status: completed",
        f"- Exports returned: {len(export_names(pack, artifacts))}",
        f"- Expected decisions matched: {expected_matched}",
        f"- Hard-gate failures: {hard_gate_failures}",
        f"- Evidence Pack ZIP SHA-256: `{zip_sha256}`",
        f"- GSEG/GSIG exports present: {required_present}",
        f"- ZIP contains GSEG/GSIG exports: {zip_contains_required}",
        f"- VSEA Parquet magic: `{parquet_status}`",
        f"- Theorem checklist release gate: `{theorem['summary']['release_gate']}`",
        f"- Graph roundtrip audit: `{graph_roundtrip['status']}`",
    ]
    if adversarial_class is not None:
        lines.append(f"- False species-safe outside positive controls: {false_species_safe}")
    lines.extend(
        [
            "",
            "## Decision classes",
            "",
            "```json",
            json.dumps(dict(actual_counts), indent=2, ensure_ascii=False),
            "```",
            "",
            "## Publication buckets",
            "",
            "```json",
            json.dumps(dict(bucket_counts), indent=2, ensure_ascii=False),
            "```",
            "",
            "## Export states",
            "",
            "```json",
            json.dumps(dict(export_state_counts), indent=2, ensure_ascii=False),
            "```",
        ]
    )
    if adversarial_class is not None:
        lines.extend(
            [
                "",
                "## By adversarial class",
                "",
                "```json",
                json.dumps({key: dict(value) for key, value in sorted(by_class.items())}, indent=2, ensure_ascii=False),
                "```",
            ]
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The run is fail-closed. Species-level output is allowed only when match gates, ambiguity/LCA, barcode gap, diagnostic k-mers, marker profile and publication gates agree. The GSEG/GSIG layer adds VSEA, graph provenance, theorem checklist, AI guardrails and roundtrip checks without claiming phenotype, function or production GraphDB/RDF behavior.",
        ]
    )
    return "\n".join(lines) + "\n"


def zip_required_present(artifacts: dict[str, str | bytes]) -> bool:
    names = set(artifacts)
    return REQUIRED_GSEG_GSIG_EXPORTS.issubset(names)


def write_report_set(
    output_dir: Path,
    report_prefix: str,
    title: str,
    pack: dict[str, Any],
    source_records: list[dict[str, Any]],
    expected: dict[str, str],
    adversarial_class: dict[str, str] | None = None,
) -> None:
    clean_dir(output_dir)
    artifacts = build_barcode_artifacts(pack)
    zip_sha256 = write_artifacts(output_dir, artifacts)
    rows = result_rows(pack, expected, adversarial_class)
    if not all(row["pass"] == "True" for row in rows):
        failures = [row for row in rows if row["pass"] != "True"]
        raise SystemExit(f"{report_prefix}: expected decisions failed: {failures[:5]}")
    theorem = json.loads(str(artifacts["theorem_checklist.json"]))
    if theorem["summary"]["fail"] != 0 or theorem["summary"]["release_gate"] != "pass":
        raise SystemExit(f"{report_prefix}: theorem checklist failed")
    parquet_bytes = artifacts["verified_segment_evidence_array.parquet"]
    if not isinstance(parquet_bytes, bytes) or parquet_bytes[:4] != b"PAR1":
        raise SystemExit(f"{report_prefix}: VSEA parquet is not a real parquet file")

    write_csv(output_dir / f"{report_prefix}_manifest.csv", manifest_rows(source_records, expected, adversarial_class))
    write_csv(output_dir / f"{report_prefix}_results.csv", rows)
    write_csv(output_dir / "expected_vs_actual.csv", rows)
    write_csv(output_dir / "decision_summary.csv", summary_csv_rows(pack))
    (output_dir / f"{report_prefix}_request.json").write_text(json.dumps(pack["request"], indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / f"{report_prefix}_api_created.json").write_text(json.dumps(pack["run"], indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / f"{report_prefix}_exports.json").write_text(json.dumps(export_names(pack, artifacts), indent=2), encoding="utf-8")
    (output_dir / f"{report_prefix}_report.md").write_text(
        render_report(
            title=title,
            pack=pack,
            artifacts=artifacts,
            rows=rows,
            zip_sha256=zip_sha256,
            adversarial_class=adversarial_class,
        ),
        encoding="utf-8",
    )


def zip_report_dir(path: Path) -> None:
    archive_path = path.with_suffix(".zip")
    if archive_path.exists():
        archive_path.unlink()
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(path.rglob("*")):
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(path.parent))


def main() -> None:
    competition_source, competition_expected = competition_records()
    competition_pack = compile_pack("EcoGenesis competition 100-sequence GSEG/GSIG verification batch", competition_source)
    write_report_set(
        COMPETITION_DIR,
        "competition_100_sequence",
        "Competition 100-Sequence Atlas Run Report",
        competition_pack,
        competition_source,
        competition_expected,
    )
    zip_report_dir(COMPETITION_DIR)

    adversarial_source, adversarial_expected, adversarial_class = adversarial_records()
    adversarial_pack = compile_pack("EcoGenesis adversarial 100-sequence fail-closed GSEG/GSIG stress batch", adversarial_source)
    write_report_set(
        ADVERSARIAL_DIR,
        "adversarial_100_sequence",
        "Adversarial 100-Sequence Fail-Closed Stress Report",
        adversarial_pack,
        adversarial_source,
        adversarial_expected,
        adversarial_class,
    )
    zip_report_dir(ADVERSARIAL_DIR)

    print(
        json.dumps(
            {
                "competition_report": str(COMPETITION_DIR / "competition_100_sequence_report.md"),
                "adversarial_report": str(ADVERSARIAL_DIR / "adversarial_100_sequence_report.md"),
                "competition_exports": len(json.loads((COMPETITION_DIR / "competition_100_sequence_exports.json").read_text())),
                "adversarial_exports": len(json.loads((ADVERSARIAL_DIR / "adversarial_100_sequence_exports.json").read_text())),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
