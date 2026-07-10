from __future__ import annotations

import csv
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from .compiler import decide_record
from .schemas import BarcodeCompilerRequest
from .scientific_gates import (
    ATTESTATION_SECRET_ENV,
    MIN_ATTESTATION_SECRET_BYTES,
    MIN_EXTERNAL_HOLDOUT_RECORDS,
    attest_external_validation_manifest,
    compiler_contract_sha256,
    scientific_release_gate,
    stable_payload_sha256,
)


HARNESS_VERSION = "ecogenesis-independent-holdout-v1"


def benchmark_contract() -> dict[str, Any]:
    return {
        "manifest": {
            "dataset_id": "stable external dataset identifier",
            "dataset_version": "immutable version",
            "source": "repository or institution independent from EcoGenesis fixtures",
            "doi_or_url": "resolvable source URL",
            "license": "data license",
            "holdout": True,
            "thresholds_frozen_before_holdout": True,
            "ground_truth_independent": True,
            "specimen_backed": True,
            "generated_from_demo_fixtures": False,
        },
        "compiler_request": "BarcodeCompilerRequest fields excluding records",
        "records": [{
            "case_id": "unique case id",
            "specimen_id": "unique voucher/material sample id",
            "marker": "marker family",
            "taxonomic_group": "independent group",
            "ground_truth": {"taxon": "accepted taxon", "rank": "species", "source_id": "voucher/accession"},
            "compiler_record": (
                "one SequenceRecord payload; any reference/gap/k-mer/chimera evidence used for a "
                "species rule must carry a trusted evidence-bundle attestation issued before the holdout run"
            ),
        }],
        "minimum_records": MIN_EXTERNAL_HOLDOUT_RECORDS,
        "clone_policy": "case fingerprints exclude IDs; repeated fixtures block release",
        "attestation": {
            "algorithm": "HMAC-SHA256 with canonical JSON and purpose separation",
            "secret_environment_variable": ATTESTATION_SECRET_ENV,
            "minimum_secret_bytes": MIN_ATTESTATION_SECRET_BYTES,
            "secret_transport": "environment only; never a CLI argument or manifest field",
            "unsigned_policy": "benchmark metrics remain informational and release_eligible=false",
            "trust_boundary": (
                "HMAC proves configured issuer and payload integrity, not biological truth; the operator must "
                "keep reference-evidence auditing independent from threshold tuning"
            ),
        },
    }


def run_holdout_benchmark(*, dataset_path: Path, output_dir: Path) -> dict[str, Any]:
    raw = dataset_path.read_bytes()
    dataset = json.loads(raw)
    manifest = dataset.get("manifest") or {}
    rows = dataset.get("records") or []
    request_payload = dict(dataset.get("compiler_request") or {})
    request_payload["records"] = [row.get("compiler_record") for row in rows]
    request = BarcodeCompilerRequest(**request_payload)
    results = []
    for row, record in zip(rows, request.records, strict=True):
        decision = decide_record(record, request)
        truth = row.get("ground_truth") or {}
        predicted_species = decision.get("scientific_decision_state") == "species-rule-pass"
        predicted_taxon = decision["candidate_taxon"]["name"] if predicted_species else None
        true_species = str(truth.get("rank") or "").lower() == "species"
        correct_species = bool(predicted_species and true_species and same_taxon(predicted_taxon, truth.get("taxon")))
        expected_genus = truth.get("genus") or str(truth.get("taxon") or "").split()[0]
        predicted_genus = genus_for_decision(decision)
        top = decision.get("top_hit") or {}
        naive_species = top.get("taxon") if top.get("rank") == "species" else None
        naive_correct = bool(true_species and naive_species and same_taxon(naive_species, truth.get("taxon")))
        results.append({
            "case_id": row.get("case_id"),
            "specimen_id": row.get("specimen_id"),
            "marker": row.get("marker"),
            "taxonomic_group": row.get("taxonomic_group"),
            "reference_completeness": decision.get("reference_completeness", {}).get("status", "missing"),
            "truth_taxon": truth.get("taxon"),
            "truth_rank": truth.get("rank"),
            "decision": decision["taxonomic_status"],
            "predicted_taxon": predicted_taxon,
            "predicted_genus": predicted_genus,
            "species_correct": correct_species,
            "false_species_rule_pass": bool(predicted_species and not correct_species),
            "genus_correct": bool(predicted_genus and same_taxon(predicted_genus, expected_genus)),
            "abstained_from_species": not predicted_species,
            "naive_top_hit_taxon": naive_species,
            "naive_species_correct": naive_correct,
            "naive_false_species": bool(naive_species and not naive_correct),
        })

    fingerprints = [independent_case_fingerprint(row) for row in rows]
    unique_cases = len(set(fingerprints))
    input_blockers = validate_dataset_contract(manifest, rows, unique_cases)
    metrics = holdout_metrics(results)
    baseline_metrics = naive_baseline_metrics(results)
    metrics["false_species_rate_delta_vs_naive"] = round(
        float(metrics["false_species_rule_pass_rate"])
        - float(baseline_metrics["naive_top_hit_false_species_rate"]),
        6,
    )
    strata = {
        "marker": stratified_metrics(results, "marker"),
        "taxonomic_group": stratified_metrics(results, "taxonomic_group"),
        "reference_completeness": stratified_metrics(results, "reference_completeness"),
    }
    external_manifest = {
        "dataset_id": manifest.get("dataset_id") or "missing",
        "dataset_version": manifest.get("dataset_version") or "missing",
        "source": manifest.get("source") or "missing",
        "doi_or_url": manifest.get("doi_or_url") or "missing",
        "license": manifest.get("license") or "missing",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "holdout": bool(manifest.get("holdout")),
        "thresholds_frozen_before_holdout": bool(manifest.get("thresholds_frozen_before_holdout")),
        "ground_truth_independent": bool(manifest.get("ground_truth_independent")),
        "specimen_backed": bool(manifest.get("specimen_backed")),
        "generated_from_demo_fixtures": bool(manifest.get("generated_from_demo_fixtures", False)),
        "record_count": len(rows),
        "unique_case_count": unique_cases,
        "marker_families": sorted({str(row.get("marker")) for row in rows if row.get("marker")}),
        "taxonomic_groups": sorted({str(row.get("taxonomic_group")) for row in rows if row.get("taxonomic_group")}),
        "evaluated_at": manifest.get("evaluated_at") or "not_supplied",
        "harness_version": HARNESS_VERSION,
        "compiler_contract_sha256": compiler_contract_sha256(request),
        "metrics": metrics,
        "baseline_metrics": baseline_metrics,
        "strata": strata,
    }
    attestation = attest_external_validation_manifest(external_manifest)
    if attestation is not None:
        external_manifest["attestation"] = attestation
    release_request = BarcodeCompilerRequest(
        **{**request.model_dump(), "external_validation_manifest": external_manifest}
    )
    release_gate = scientific_release_gate(release_request)
    blockers = [*input_blockers, *release_gate["blockers"]]
    summary = {
        "status": "pass" if not blockers else "blocked",
        "release_eligible": not blockers,
        "blockers": sorted(set(blockers)),
        "metrics": metrics,
        "baseline_metrics": baseline_metrics,
        "strata": strata,
        "manifest": external_manifest,
        "attestation": release_gate.get("attestation_verification", {
            "status": "unsigned",
            "verified": False,
            "evidence_use": "informational_only",
        }),
        "contract": benchmark_contract(),
    }
    write_outputs(output_dir, results, summary)
    return summary


def validate_dataset_contract(manifest: dict[str, Any], rows: list[dict[str, Any]], unique_cases: int) -> list[str]:
    blockers = []
    for field in ("dataset_id", "dataset_version", "source", "doi_or_url", "license", "evaluated_at"):
        if not str(manifest.get(field) or "").strip():
            blockers.append(f"holdout manifest missing {field}")
    for field in ("holdout", "thresholds_frozen_before_holdout", "ground_truth_independent", "specimen_backed"):
        if manifest.get(field) is not True:
            blockers.append(f"holdout manifest requires {field}=true")
    if manifest.get("generated_from_demo_fixtures") is not False:
        blockers.append("holdout dataset must explicitly set generated_from_demo_fixtures=false")
    if len(rows) < MIN_EXTERNAL_HOLDOUT_RECORDS:
        blockers.append(f"holdout requires at least {MIN_EXTERNAL_HOLDOUT_RECORDS} records")
    if unique_cases != len(rows):
        blockers.append(f"repeated fixture fingerprints detected: {len(rows) - unique_cases} duplicate cases")
    case_ids = [row.get("case_id") for row in rows]
    specimen_ids = [row.get("specimen_id") for row in rows]
    if any(not value for value in case_ids) or len(set(case_ids)) != len(rows):
        blockers.append("case_id values must be present and unique")
    if any(not value for value in specimen_ids) or len(set(specimen_ids)) != len(rows):
        blockers.append("specimen_id values must be present and unique")
    for index, row in enumerate(rows, start=1):
        truth = row.get("ground_truth") or {}
        if not all(truth.get(field) for field in ("taxon", "rank", "source_id")):
            blockers.append(f"record {index} lacks independent ground_truth taxon/rank/source_id")
    return blockers


def independent_case_fingerprint(row: dict[str, Any]) -> str:
    payload = deepcopy(row)
    payload.pop("case_id", None)
    payload.pop("specimen_id", None)
    record = payload.get("compiler_record") or {}
    record.pop("sequence_id", None)
    metadata = record.get("metadata") or {}
    for field in ("occurrenceID", "sequenceID", "benchmarkCase", "eventID", "materialSampleID"):
        metadata.pop(field, None)
    return stable_payload_sha256(payload)


def holdout_metrics(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    total = len(rows)
    truth_species = sum(str(row["truth_rank"] or "").lower() == "species" for row in rows)
    species_calls = sum(not row["abstained_from_species"] for row in rows)
    species_true = sum(row["species_correct"] for row in rows)
    false_species = sum(row["false_species_rule_pass"] for row in rows)
    genus_calls = sum(bool(row["predicted_genus"]) for row in rows)
    genus_true = sum(row["genus_correct"] for row in rows)
    precision_ci = wilson_interval(species_true, species_calls)
    recall_ci = wilson_interval(species_true, truth_species)
    false_ci = wilson_interval(false_species, total)
    return {
        "records": total,
        "species_precision": round(species_true / species_calls, 6) if species_calls else 0.0,
        "species_precision_ci_low": precision_ci[0],
        "species_precision_ci_high": precision_ci[1],
        "species_recall": round(species_true / truth_species, 6) if truth_species else 0.0,
        "species_recall_ci_low": recall_ci[0],
        "species_recall_ci_high": recall_ci[1],
        "genus_precision": round(genus_true / genus_calls, 6) if genus_calls else 0.0,
        "abstention_rate": round((total - species_calls) / total, 6) if total else 1.0,
        "false_species_rule_pass_rate": round(false_species / total, 6) if total else 1.0,
        "false_species_rule_pass_rate_ci_low": false_ci[0],
        "false_species_rule_pass_rate_ci_high": false_ci[1],
        "false_species_rule_pass_count": false_species,
    }


def naive_baseline_metrics(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    calls = sum(bool(row.get("naive_top_hit_taxon")) for row in rows)
    correct = sum(bool(row.get("naive_species_correct")) for row in rows)
    false = sum(bool(row.get("naive_false_species")) for row in rows)
    return {
        "naive_top_hit_species_calls": calls,
        "naive_top_hit_species_precision": round(correct / calls, 6) if calls else 0.0,
        "naive_top_hit_false_species_rate": round(false / len(rows), 6) if rows else 1.0,
    }


def stratified_metrics(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, float | int]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(str(row.get(field) or "missing"), []).append(row)
    return {name: holdout_metrics(group) for name, group in sorted(groups.items())}


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    if trials <= 0:
        return (0.0, 1.0)
    proportion = successes / trials
    denominator = 1 + z * z / trials
    centre = (proportion + z * z / (2 * trials)) / denominator
    margin = z * ((proportion * (1 - proportion) / trials + z * z / (4 * trials * trials)) ** 0.5) / denominator
    return (round(max(0.0, centre - margin), 6), round(min(1.0, centre + margin), 6))


def genus_for_decision(decision: dict[str, Any]) -> str | None:
    candidate = decision["candidate_taxon"]
    decision_state = decision.get("scientific_decision_state")
    if candidate["rank"] == "genus" and decision_state == "genus-safe":
        return candidate["name"]
    if candidate["rank"] == "species" and decision_state == "species-rule-pass":
        return str(candidate["name"]).split()[0]
    return None


def same_taxon(first: Any, second: Any) -> bool:
    return str(first or "").strip().casefold() == str(second or "").strip().casefold()


def write_outputs(output_dir: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "holdout_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "external_validation_manifest.json").write_text(
        json.dumps(summary["manifest"], indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if rows:
        with (output_dir / "holdout_case_results.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
