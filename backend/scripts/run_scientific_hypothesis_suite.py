from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evidence.pipeline import run_evidence_passport
from app.evidence.schemas import EvidenceRunRequest


PRIMARY_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "aedes-spain",
        "label": "Aedes albopictus · Spain",
        "taxon": "Aedes albopictus",
        "taxon_key": 1651430,
        "region_name": "Spain live GBIF bbox",
        "bbox": [-10.0, 35.0, 4.5, 44.5],
        "purpose": "invasive_watch",
    },
    {
        "id": "aedes-italy",
        "label": "Aedes albopictus · Italy",
        "taxon": "Aedes albopictus",
        "taxon_key": 1651430,
        "region_name": "Italy live GBIF bbox",
        "bbox": [6.6, 36.4, 18.8, 47.1],
        "purpose": "invasive_watch",
    },
    {
        "id": "aedes-france",
        "label": "Aedes albopictus · France",
        "taxon": "Aedes albopictus",
        "taxon_key": 1651430,
        "region_name": "France live GBIF bbox",
        "bbox": [-5.2, 41.3, 9.7, 51.2],
        "purpose": "invasive_watch",
    },
    {
        "id": "quercus-western-europe",
        "label": "Quercus robur · Western Europe",
        "taxon": "Quercus robur",
        "taxon_key": 2878688,
        "region_name": "Western Europe live bbox",
        "bbox": [-10.0, 42.0, 12.0, 56.0],
        "purpose": "sampling_gaps",
    },
    {
        "id": "quercus-germany",
        "label": "Quercus robur · Germany",
        "taxon": "Quercus robur",
        "taxon_key": 2878688,
        "region_name": "Germany live GBIF bbox",
        "bbox": [5.8, 47.2, 15.1, 55.1],
        "purpose": "sampling_gaps",
    },
    {
        "id": "lynx-iberia",
        "label": "Lynx pardinus · Iberian Peninsula",
        "taxon": "Lynx pardinus",
        "taxon_key": 2435261,
        "region_name": "Iberian Peninsula live bbox",
        "bbox": [-10.0, 35.0, 4.5, 44.5],
        "purpose": "dataset_quality_review",
    },
    {
        "id": "apis-western-europe",
        "label": "Apis mellifera · Western Europe",
        "taxon": "Apis mellifera",
        "taxon_key": 1341976,
        "region_name": "Western Europe live bbox",
        "bbox": [-10.0, 42.0, 12.0, 56.0],
        "purpose": "dataset_quality_review",
    },
    {
        "id": "apis-france",
        "label": "Apis mellifera · France",
        "taxon": "Apis mellifera",
        "taxon_key": 1341976,
        "region_name": "France live GBIF bbox",
        "bbox": [-5.2, 41.3, 9.7, 51.2],
        "purpose": "sampling_gaps",
    },
    {
        "id": "passer-western-europe",
        "label": "Passer domesticus · Western Europe",
        "taxon": "Passer domesticus",
        "taxon_key": 5231190,
        "region_name": "Western Europe live bbox",
        "bbox": [-10.0, 42.0, 12.0, 56.0],
        "purpose": "sampling_gaps",
    },
    {
        "id": "passer-united-states",
        "label": "Passer domesticus · United States",
        "taxon": "Passer domesticus",
        "taxon_key": 5231190,
        "region_name": "United States live GBIF bbox",
        "bbox": [-125.0, 24.0, -66.5, 49.5],
        "purpose": "dataset_quality_review",
    },
]


RESERVE_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "apis-spain",
        "label": "Apis mellifera · Spain",
        "taxon": "Apis mellifera",
        "taxon_key": 1341976,
        "region_name": "Spain live GBIF bbox",
        "bbox": [-10.0, 35.0, 4.5, 44.5],
        "purpose": "dataset_quality_review",
    },
    {
        "id": "passer-united-kingdom",
        "label": "Passer domesticus · United Kingdom",
        "taxon": "Passer domesticus",
        "taxon_key": 5231190,
        "region_name": "United Kingdom live GBIF bbox",
        "bbox": [-8.7, 49.8, 1.9, 60.9],
        "purpose": "sampling_gaps",
    },
    {
        "id": "quercus-france",
        "label": "Quercus robur · France",
        "taxon": "Quercus robur",
        "taxon_key": 2878688,
        "region_name": "France live GBIF bbox",
        "bbox": [-5.2, 41.3, 9.7, 51.2],
        "purpose": "sampling_gaps",
    },
    {
        "id": "aedes-japan",
        "label": "Aedes albopictus · Japan",
        "taxon": "Aedes albopictus",
        "taxon_key": 1651430,
        "region_name": "Japan live GBIF bbox",
        "bbox": [129.0, 30.0, 146.0, 46.0],
        "purpose": "invasive_watch",
    },
    {
        "id": "passer-canada",
        "label": "Passer domesticus · Canada",
        "taxon": "Passer domesticus",
        "taxon_key": 5231190,
        "region_name": "Canada live GBIF bbox",
        "bbox": [-141.0, 41.7, -52.6, 83.1],
        "purpose": "dataset_quality_review",
    },
]


BOTTLENECKS = [
    "GBIF API can be unavailable or degraded; empty fallback runs are not counted as valid live evidence.",
    "The current GBIF API path reads search results, not a DOI-backed GBIF download; formal publication still needs a DOI or derived dataset citation.",
    "The current client uses the first occurrence-search page for each scenario; large research studies need GBIF download API or pagination.",
    "A bbox is not the same as an administrative country boundary.",
    "GBIF occurrence records do not prove species absence.",
    "Occurrence clusters can reflect observer effort rather than true abundance or distribution.",
    "Population trend claims are blocked without temporal sampling-bias correction.",
    "High coordinate uncertainty weakens fine-scale claims.",
    "Missing eventDate/year weakens temporal claims.",
    "Single-dataset dominance can bias apparent evidence patterns.",
    "TaxonKey improves reproducibility, but synonyms and taxonomic changes still need review.",
    "Barcode/protein layers are outside this live occurrence test because the GBIF occurrence API is not Sequence ID.",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a 1000-record live GBIF hypothesis suite.")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/scientific-theory-suite"))
    parser.add_argument("--target-records", type=int, default=1000)
    parser.add_argument("--target-claims", type=int, default=100)
    parser.add_argument("--max-records", type=int, default=120)
    parser.add_argument("--fresh", action="store_true", help="Delete the output directory before writing the new report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    os.environ.setdefault("EVIDENCE_DATA_DIR", str(repo_root / "data"))
    output_dir = args.output_dir if args.output_dir.is_absolute() else repo_root / args.output_dir
    if args.fresh and output_dir.exists():
        shutil.rmtree(output_dir)
    raw_dir = output_dir / "raw_packs"
    raw_dir.mkdir(parents=True, exist_ok=True)

    attempted: list[dict[str, Any]] = []
    successful: list[dict[str, Any]] = []
    deduped_records: dict[str, dict[str, Any]] = {}
    duplicate_count = 0

    for scenario in [*PRIMARY_SCENARIOS, *RESERVE_SCENARIOS]:
        if len(successful) >= 10 and len(deduped_records) >= args.target_records:
            break
        result = run_scenario(scenario, max_records=args.max_records, raw_dir=raw_dir)
        attempted.append(result)
        pack = result.get("pack")
        if not result["eligible"] or not pack:
            continue
        before = len(deduped_records)
        duplicate_count += add_deduped_records(deduped_records, scenario, pack)
        result["deduped_records_added"] = len(deduped_records) - before
        successful.append(result)

    selected_records = list(deduped_records.values())[: args.target_records]
    claim_scenarios = sorted(successful, key=lambda row: row["records_used"], reverse=True)[:10]
    claims = build_claims(claim_scenarios)[: args.target_claims]
    scenario_rows = [scenario_metric_row(row) for row in attempted]
    bottleneck_text = build_bottleneck_report(attempted, successful, selected_records, claims, duplicate_count)
    run_index = build_run_index(args, attempted, selected_records, claims, duplicate_count)

    write_csv(output_dir / "records_1000.csv", selected_records)
    write_csv(output_dir / "scenario_metrics.csv", scenario_rows)
    write_csv(output_dir / "theory_claims_100.csv", claims)
    write_json(output_dir / "run_index.json", run_index)
    write_text(output_dir / "bottlenecks_and_errors.md", bottleneck_text)
    write_text(output_dir / "summary.md", build_summary(run_index, scenario_rows, claims))
    write_text(output_dir / "scientific_theory_report.html", build_html_report(run_index, scenario_rows, claims, bottleneck_text))

    print(json.dumps(run_index["acceptance"], indent=2, ensure_ascii=False))
    if not all(run_index["acceptance"].values()):
        raise SystemExit(1)


def run_scenario(scenario: dict[str, Any], *, max_records: int, raw_dir: Path) -> dict[str, Any]:
    request = EvidenceRunRequest(
        taxon=scenario["taxon"],
        taxon_key=scenario["taxon_key"],
        region_name=scenario["region_name"],
        bbox=scenario["bbox"],
        purpose=scenario["purpose"],
        source_mode="online_with_empty_fallback",
        use_fixture=False,
        max_records=max_records,
    )
    result: dict[str, Any] = {
        "scenario": scenario,
        "scenario_id": scenario["id"],
        "label": scenario["label"],
        "eligible": False,
        "error": "",
        "records_used": 0,
        "deduped_records_added": 0,
    }
    try:
        pack = run_evidence_passport(request)
        write_json(raw_dir / f"{scenario['id']}.json", pack)
        source = pack["source_summary"]
        eligible = source.get("used_source_mode") == "online" and source.get("gbif_api_status") == "ok" and not source.get("fallback_used")
        result.update(
            {
                "eligible": eligible,
                "pack": pack,
                "run_id": pack["run"]["run_id"],
                "records_used": pack["passport"]["records_used"],
                "datasets_used": pack["passport"]["datasets_used"],
                "used_source_mode": source.get("used_source_mode"),
                "gbif_api_status": source.get("gbif_api_status"),
                "fallback_used": source.get("fallback_used"),
                "gbif_result_count": source.get("gbif_result_count"),
                "gbif_returned_records": source.get("gbif_returned_records"),
            }
        )
    except Exception as exc:  # noqa: BLE001 - report suite must capture every scenario failure.
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def add_deduped_records(deduped: dict[str, dict[str, Any]], scenario: dict[str, Any], pack: dict[str, Any]) -> int:
    duplicates = 0
    for record in pack.get("normalized_records", []):
        gbif_id = str(record.get("gbif_id") or "").strip()
        key = gbif_id or f"{scenario['id']}:{record.get('dataset_key')}:{record.get('scientific_name')}:{record.get('latitude')}:{record.get('longitude')}:{record.get('event_date')}"
        if key in deduped:
            duplicates += 1
            continue
        deduped[key] = flatten_record(record, scenario, pack)
    return duplicates


def flatten_record(record: dict[str, Any], scenario: dict[str, Any], pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": scenario["id"],
        "run_id": pack["run"]["run_id"],
        "gbif_id": record.get("gbif_id"),
        "datasetKey": record.get("dataset_key"),
        "datasetTitle": record.get("dataset_title"),
        "publisher": record.get("publisher"),
        "license": record.get("license"),
        "scientificName": record.get("scientific_name"),
        "acceptedTaxonKey": record.get("accepted_taxon_key"),
        "taxonKey": record.get("taxon_key"),
        "decimalLatitude": record.get("latitude"),
        "decimalLongitude": record.get("longitude"),
        "eventDate": record.get("event_date"),
        "year": record.get("year"),
        "coordinateUncertaintyInMeters": record.get("coordinate_uncertainty_m"),
        "country": record.get("country"),
        "countryCode": record.get("country_code"),
        "basisOfRecord": record.get("basis_of_record"),
        "issues": ";".join(record.get("issues") or []),
    }


def build_claims(successful: list[dict[str, Any]]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for result in successful:
        scenario = result["scenario"]
        pack = result["pack"]
        for index, claim in enumerate(claim_templates(scenario, pack), start=1):
            claims.append(
                {
                    "claim_id": f"{scenario['id']}-H{index:02d}",
                    "scenario_id": scenario["id"],
                    "taxon": scenario["taxon"],
                    "region": scenario["region_name"],
                    **claim,
                    "records_used": pack["passport"]["records_used"],
                    "datasets_used": pack["passport"]["datasets_used"],
                }
            )
    return claims


def claim_templates(scenario: dict[str, Any], pack: dict[str, Any]) -> list[dict[str, Any]]:
    quality = pack["quality_metrics"]
    grid = pack["grid_metrics"]["meta"]
    readiness = pack["evidence_readiness"]
    citation = pack["citation_autopilot"]
    records_used = pack["passport"]["records_used"]
    datasets_used = pack["passport"]["datasets_used"]
    score = readiness["score"]
    high_uncertainty = quality["high_uncertainty_count"]
    missing_dates = quality["missing_date_count"]
    date_rate = quality["date_present_rate"]
    recent_rate = quality["recent_record_rate"]
    valid_coordinate_rate = quality["valid_coordinate_rate"]
    empty_cells = grid["empty_cell_count"]
    survey_priority_cells = grid["survey_priority_cells"]
    dataset_share = top_dataset_share(pack)
    return [
        claim(
            "Occurrence evidence exists in selected region",
            "supported" if records_used > 0 else "blocked",
            {"records_used": records_used, "gbif_result_count": pack["source_summary"].get("gbif_result_count")},
            "This supports only a retained GBIF-mediated occurrence-evidence claim, not abundance or absence.",
            "Use records as evidence context and preserve source_summary.json.",
        ),
        claim(
            "Evidence readiness is sufficient or insufficient for selected purpose",
            "supported" if score >= 75 else "weak" if score >= 55 else "blocked",
            {"readiness_score": score, "purpose": scenario["purpose"], "components": readiness.get("components")},
            "The score is purpose-aware and must be interpreted with the component scores.",
            "Inspect the weakest readiness components before reuse.",
        ),
        claim(
            "Dataset provenance is multi-source or single-source biased",
            "supported" if datasets_used >= 2 and dataset_share < 0.8 else "weak" if datasets_used >= 1 else "blocked",
            {"datasets_used": datasets_used, "top_dataset_share": round(dataset_share, 4)},
            "Single-dataset dominance can reflect publisher or platform bias.",
            "Use dataset_contributions.csv to audit source concentration.",
        ),
        claim(
            "Coordinate quality supports or weakens fine-scale interpretation",
            "supported" if valid_coordinate_rate >= 0.95 and high_uncertainty == 0 else "weak" if valid_coordinate_rate >= 0.8 else "requires_verification",
            {"valid_coordinate_rate": valid_coordinate_rate, "high_uncertainty_count": high_uncertainty},
            "Fine-scale interpretation is unsafe when coordinates are uncertain or invalid.",
            "Review records with high coordinate uncertainty before local decisions.",
        ),
        claim(
            "Temporal completeness supports or blocks time-based interpretation",
            "supported" if date_rate >= 0.9 else "weak" if date_rate >= 0.7 else "requires_verification",
            {"date_present_rate": date_rate, "missing_date_count": missing_dates},
            "Temporal claims need eventDate/year; missing dates weaken any time-based inference.",
            "Repair missing eventDate/year before temporal interpretation.",
        ),
        claim(
            "Recent evidence exists or needs verification",
            "supported" if recent_rate >= 0.5 else "weak" if recent_rate > 0 else "requires_verification",
            {"recent_record_rate": recent_rate, "current_year_window": "last 10 years"},
            "Recent records are not trend evidence; they only show recent retained GBIF evidence.",
            "Separate recent occurrence evidence from population trend claims.",
        ),
        claim(
            "Survey-priority cells identify where more sampling is needed",
            "requires_verification" if survey_priority_cells else "supported",
            {"survey_priority_cells": survey_priority_cells, "under_sampled_cells": grid["under_sampled_cells"]},
            "Survey priorities are planning hints, not confirmed biodiversity gaps.",
            "Use priority cells to design field/literature review, not to infer absence.",
        ),
        claim(
            "Empty cells are no-evidence cells, not absence evidence",
            "blocked",
            {"empty_cell_count": empty_cells, "grid_size": grid["grid_size"]},
            "GBIF occurrence data cannot prove species absence in empty cells.",
            "Label empty cells as no-evidence and avoid absence claims.",
        ),
        claim(
            "Observed GBIF distribution is not true species distribution",
            "blocked",
            {"records_used": records_used, "occupied_cell_count": grid["occupied_cell_count"]},
            "Observed GBIF distribution is shaped by sampling effort, data sharing and dataset coverage.",
            "Treat maps as evidence context, not a distribution model.",
        ),
        claim(
            "DOI/citation readiness is incomplete until GBIF download DOI or derived dataset is attached",
            "supported" if citation["citation_status"] == "doi_backed" else "requires_verification",
            {"citation_status": citation["citation_status"], "doi_ready": citation["citation_status"] == "doi_backed"},
            "API search results are not a DOI-backed publication dataset.",
            "Create a GBIF download DOI or derived dataset recipe before publication use.",
        ),
    ]


def claim(hypothesis: str, status: str, evidence_fields: dict[str, Any], caveat: str, action: str) -> dict[str, Any]:
    return {
        "hypothesis": hypothesis,
        "status": status,
        "evidence_fields": json.dumps(evidence_fields, ensure_ascii=False, sort_keys=True),
        "caveat": caveat,
        "recommended_action": action,
    }


def top_dataset_share(pack: dict[str, Any]) -> float:
    rows = pack.get("dataset_contributions") or []
    total = sum(int(row.get("record_count") or 0) for row in rows)
    if total <= 0:
        return 0.0
    return max(int(row.get("record_count") or 0) for row in rows) / total


def scenario_metric_row(result: dict[str, Any]) -> dict[str, Any]:
    pack = result.get("pack") or {}
    quality = pack.get("quality_metrics") or {}
    grid = (pack.get("grid_metrics") or {}).get("meta") or {}
    citation = pack.get("citation_autopilot") or {}
    scenario = result["scenario"]
    return {
        "scenario_id": scenario["id"],
        "label": scenario["label"],
        "taxon": scenario["taxon"],
        "taxon_key": scenario["taxon_key"],
        "region_name": scenario["region_name"],
        "purpose": scenario["purpose"],
        "eligible": result["eligible"],
        "run_id": result.get("run_id", ""),
        "used_source_mode": result.get("used_source_mode", ""),
        "gbif_api_status": result.get("gbif_api_status", ""),
        "fallback_used": result.get("fallback_used", ""),
        "gbif_result_count": result.get("gbif_result_count", ""),
        "gbif_returned_records": result.get("gbif_returned_records", ""),
        "records_used": result.get("records_used", 0),
        "deduped_records_added": result.get("deduped_records_added", 0),
        "datasets_used": result.get("datasets_used", 0),
        "readiness_score": (pack.get("evidence_readiness") or {}).get("score", ""),
        "valid_coordinate_rate": quality.get("valid_coordinate_rate", ""),
        "date_present_rate": quality.get("date_present_rate", ""),
        "recent_record_rate": quality.get("recent_record_rate", ""),
        "high_uncertainty_count": quality.get("high_uncertainty_count", ""),
        "missing_date_count": quality.get("missing_date_count", ""),
        "empty_cell_count": grid.get("empty_cell_count", ""),
        "survey_priority_cells": grid.get("survey_priority_cells", ""),
        "citation_status": citation.get("citation_status", ""),
        "error": result.get("error", ""),
    }


def build_run_index(
    args: argparse.Namespace,
    attempted: list[dict[str, Any]],
    records: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    duplicate_count: int,
) -> dict[str, Any]:
    eligible = [row for row in attempted if row["eligible"]]
    acceptance = {
        "minimum_1000_deduplicated_records": len(records) >= args.target_records,
        "minimum_10_successful_online_scenarios": len(eligible) >= 10,
        "no_fixture_records_counted": all(not row.get("fallback_used") for row in eligible),
        "minimum_100_hypothesis_claims": len(claims) >= args.target_claims,
        "every_claim_has_status_evidence_and_caveat": all(row.get("status") and row.get("evidence_fields") and row.get("caveat") for row in claims),
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_records": args.target_records,
        "target_claims": args.target_claims,
        "attempted_scenarios": len(attempted),
        "successful_online_scenarios": len(eligible),
        "deduplicated_records_written": len(records),
        "hypothesis_claims_written": len(claims),
        "duplicate_records_skipped": duplicate_count,
        "acceptance": acceptance,
        "scenario_order": [row["scenario_id"] for row in attempted],
        "successful_scenarios": [row["scenario_id"] for row in eligible],
    }


def build_bottleneck_report(
    attempted: list[dict[str, Any]],
    successful: list[dict[str, Any]],
    records: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    duplicate_count: int,
) -> str:
    scenario_rows = [scenario_metric_row(row) for row in attempted]
    low_record = [row for row in scenario_rows if row["eligible"] and int(row["deduped_records_added"] or 0) < 100]
    failed = [row for row in scenario_rows if not row["eligible"]]
    high_uncertainty_total = sum(int(row.get("high_uncertainty_count") or 0) for row in scenario_rows if row["eligible"])
    missing_date_total = sum(int(row.get("missing_date_count") or 0) for row in scenario_rows if row["eligible"])
    single_dataset = [row for row in scenario_rows if row["eligible"] and int(row.get("datasets_used") or 0) <= 1]
    blocked_claims = sum(1 for row in claims if row["status"] == "blocked")
    verification_claims = sum(1 for row in claims if row["status"] == "requires_verification")
    lines = [
        "# Bottlenecks And Errors",
        "",
        "## Suite Totals",
        "",
        f"- Successful online scenarios: {len(successful)}",
        f"- Deduplicated records written: {len(records)}",
        f"- Duplicate records skipped: {duplicate_count}",
        f"- Hypothesis claims: {len(claims)}",
        f"- Blocked claims: {blocked_claims}",
        f"- Requires-verification claims: {verification_claims}",
        f"- High coordinate uncertainty records across scenarios: {high_uncertainty_total}",
        f"- Missing eventDate/year records across scenarios: {missing_date_total}",
        "",
        "## Fixed Methodological Bottlenecks",
        "",
        *[f"- {item}" for item in BOTTLENECKS],
        "",
        "## Scenario Failures Or Empty Fallbacks",
        "",
    ]
    lines.extend([f"- {row['scenario_id']}: {row['error'] or row['used_source_mode']}" for row in failed] or ["- None detected."])
    lines.extend(["", "## Low Record / High Duplicate Scenarios", ""])
    lines.extend([f"- {row['scenario_id']}: {row['deduped_records_added']} deduped records added from {row['records_used']} retained records." for row in low_record] or ["- None below the 100-record target."])
    lines.extend(["", "## Single Dataset Bias", ""])
    lines.extend([f"- {row['scenario_id']}: only {row['datasets_used']} dataset(s) represented." for row in single_dataset] or ["- No scenario had one or zero datasets."])
    return "\n".join(lines) + "\n"


def build_summary(run_index: dict[str, Any], scenario_rows: list[dict[str, Any]], claims: list[dict[str, Any]]) -> str:
    status_counts: dict[str, int] = {}
    for item in claims:
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1
    lines = [
        "# Scientific Hypothesis Suite Report",
        "",
        "This live suite tests whether EcoGenesis can convert GBIF-mediated occurrence data into safe scientific hypotheses.",
        "",
        "## Acceptance",
        "",
        *[f"- {key}: `{value}`" for key, value in run_index["acceptance"].items()],
        "",
        "## Totals",
        "",
        f"- Deduplicated live GBIF records: `{run_index['deduplicated_records_written']}`",
        f"- Successful online scenarios: `{run_index['successful_online_scenarios']}`",
        f"- Hypothesis claims: `{run_index['hypothesis_claims_written']}`",
        f"- Duplicate records skipped: `{run_index['duplicate_records_skipped']}`",
        f"- Claim status counts: `{json.dumps(status_counts, ensure_ascii=False, sort_keys=True)}`",
        "",
        "## Scenario Metrics",
        "",
        "| Scenario | Source | GBIF | Records | Datasets | Score | Missing dates | High uncertainty |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in scenario_rows:
        lines.append(
            f"| {row['scenario_id']} | {row['used_source_mode']} | {row['gbif_api_status']} | {row['records_used']} | {row['datasets_used']} | {row['readiness_score']} | {row['missing_date_count']} | {row['high_uncertainty_count']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The suite supports limited evidence-context claims, weakens claims affected by sampling or metadata bias, blocks absence/distribution/trend overclaims, and marks DOI/citation completion as required verification.",
            "",
        ]
    )
    return "\n".join(lines)


def build_html_report(run_index: dict[str, Any], scenario_rows: list[dict[str, Any]], claims: list[dict[str, Any]], bottlenecks: str) -> str:
    claim_rows = "\n".join(
        "<tr>"
        f"<td>{escape(row['claim_id'])}</td>"
        f"<td>{escape(row['status'])}</td>"
        f"<td>{escape(row['taxon'])}</td>"
        f"<td>{escape(row['region'])}</td>"
        f"<td>{escape(row['hypothesis'])}</td>"
        f"<td>{escape(row['caveat'])}</td>"
        "</tr>"
        for row in claims
    )
    scenario_html = "\n".join(
        "<tr>"
        f"<td>{escape(str(row['scenario_id']))}</td>"
        f"<td>{escape(str(row['used_source_mode']))}</td>"
        f"<td>{escape(str(row['gbif_api_status']))}</td>"
        f"<td>{escape(str(row['records_used']))}</td>"
        f"<td>{escape(str(row['datasets_used']))}</td>"
        f"<td>{escape(str(row['readiness_score']))}</td>"
        "</tr>"
        for row in scenario_rows
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>EcoGenesis Scientific Hypothesis Suite</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin: 32px; color: #1d2b24; background: #f6f8f4; }}
    h1, h2 {{ color: #10251b; }}
    table {{ border-collapse: collapse; width: 100%; margin: 18px 0 28px; background: white; }}
    th, td {{ border: 1px solid #dce6dd; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #113425; color: white; }}
    code, pre {{ background: #edf2ee; padding: 2px 4px; border-radius: 4px; }}
    .ok {{ color: #0e6b45; font-weight: 800; }}
  </style>
</head>
<body>
  <h1>EcoGenesis Scientific Hypothesis Suite</h1>
  <p>Live GBIF records: <strong>{run_index['deduplicated_records_written']}</strong>. Hypothesis claims: <strong>{run_index['hypothesis_claims_written']}</strong>.</p>
  <h2>Acceptance</h2>
  <pre>{escape(json.dumps(run_index['acceptance'], indent=2, ensure_ascii=False))}</pre>
  <h2>Scenario Metrics</h2>
  <table><thead><tr><th>Scenario</th><th>Source</th><th>GBIF</th><th>Records</th><th>Datasets</th><th>Score</th></tr></thead><tbody>{scenario_html}</tbody></table>
  <h2>100 Hypothesis Claims</h2>
  <table><thead><tr><th>ID</th><th>Status</th><th>Taxon</th><th>Region</th><th>Hypothesis</th><th>Caveat</th></tr></thead><tbody>{claim_rows}</tbody></table>
  <h2>Bottlenecks And Errors</h2>
  <pre>{escape(bottlenecks)}</pre>
</body>
</html>
"""


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
